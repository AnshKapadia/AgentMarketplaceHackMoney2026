"""Withdrawal service for converting AGNT to USDC and sending to agents."""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from typing import Dict

from web3 import Web3
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.models.withdrawal_transaction import WithdrawalTransaction
from app.models.agent import Agent
from app.services.uniswap_service import uniswap_service

logger = logging.getLogger(__name__)


class WithdrawalService:
    """Service for handling agent withdrawals (AGNT → USDC)."""

    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))
        self.min_withdrawal = settings.WITHDRAWAL_MIN_AMOUNT
        self.fee_percent = settings.WITHDRAWAL_FEE_PERCENT
        self.rate_limit_per_hour = settings.WITHDRAWAL_RATE_LIMIT_PER_HOUR

        # Platform wallet for executing withdrawals
        self.platform_private_key = settings.PLATFORM_WALLET_PRIVATE_KEY
        if self.platform_private_key:
            self.platform_account = self.web3.eth.account.from_key(self.platform_private_key)
            self.platform_address = self.platform_account.address
        else:
            self.platform_account = None
            self.platform_address = None
            logger.warning("Platform wallet not configured - withdrawals will not execute")

        # Token contracts
        self.agnt_address = settings.AGENTCOIN_ADDRESS
        self.usdc_address = settings.USDC_ADDRESS

        # ERC20 ABI for transfers and approvals
        self.erc20_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "spender", "type": "address"},
                    {"name": "value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

    async def validate_withdrawal_request(
        self,
        agent: Agent,
        agnt_amount: Decimal,
        recipient_address: str,
        db: AsyncSession
    ) -> Dict:
        """
        Validate a withdrawal request.

        Returns:
            Dict with 'valid': bool and optional 'error': str
        """
        # Check minimum withdrawal amount
        if agnt_amount < self.min_withdrawal:
            return {
                'valid': False,
                'error': f"Minimum withdrawal amount is {self.min_withdrawal} AGNT"
            }

        # Check agent has sufficient balance
        if agent.balance < agnt_amount:
            return {
                'valid': False,
                'error': f"Insufficient balance. Available: {agent.balance} AGNT"
            }

        # Check recipient address is valid
        if not Web3.is_address(recipient_address):
            return {
                'valid': False,
                'error': f"Invalid recipient address: {recipient_address}"
            }

        # Check rate limiting (max withdrawals per hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        result = await db.execute(
            select(func.count(WithdrawalTransaction.id))
            .where(
                WithdrawalTransaction.agent_id == agent.id,
                WithdrawalTransaction.created_at >= one_hour_ago
            )
        )
        recent_withdrawals = result.scalar()

        if recent_withdrawals >= self.rate_limit_per_hour:
            return {
                'valid': False,
                'error': f"Rate limit exceeded. Max {self.rate_limit_per_hour} withdrawals per hour."
            }

        return {'valid': True}

    async def create_withdrawal_request(
        self,
        agent: Agent,
        agnt_amount: Decimal,
        recipient_address: str,
        db: AsyncSession
    ) -> WithdrawalTransaction:
        """
        Create a withdrawal request and deduct balance immediately.

        Args:
            agent: Agent requesting withdrawal
            agnt_amount: Amount of AGNT to withdraw (before fees)
            recipient_address: Wallet address to receive USDC
            db: Database session

        Returns:
            Created WithdrawalTransaction

        Raises:
            ValueError: If validation fails
        """
        # Validate request
        validation = await self.validate_withdrawal_request(
            agent, agnt_amount, recipient_address, db
        )
        if not validation['valid']:
            raise ValueError(validation['error'])

        # Calculate fee
        fee_agnt = agnt_amount * (self.fee_percent / Decimal("100"))
        agnt_after_fee = agnt_amount - fee_agnt

        # Get expected USDC amount (estimate)
        try:
            usdc_estimate = await uniswap_service.get_quote_agnt_to_usdc(agnt_after_fee)
        except Exception as e:
            logger.error(f"Error getting withdrawal quote: {e}")
            usdc_estimate = Decimal("0")

        # Deduct balance immediately
        agent.balance -= agnt_amount
        agent.total_spent += agnt_amount

        # Create withdrawal record
        withdrawal = WithdrawalTransaction(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            agnt_amount_in=agnt_amount,
            usdc_amount_out=usdc_estimate,  # Will be updated after actual swap
            fee_agnt=fee_agnt,
            exchange_rate=Decimal("0"),  # Will be updated after swap
            recipient_address=recipient_address,
            status="pending",
            created_at=datetime.utcnow()
        )

        db.add(withdrawal)
        await db.commit()
        await db.refresh(withdrawal)

        logger.info(
            f"Withdrawal request created: {withdrawal.id} for agent {agent.id}, "
            f"amount: {agnt_amount} AGNT (fee: {fee_agnt} AGNT)"
        )

        return withdrawal

    async def execute_withdrawal(
        self,
        withdrawal: WithdrawalTransaction,
        db: AsyncSession
    ) -> bool:
        """
        Execute the withdrawal: swap AGNT to USDC via Uniswap V4 and transfer.

        Uses the official Uniswap V4 SDK (Node.js) to properly encode and
        execute the swap through the UniversalRouter.
        Refunds AGNT to agent balance on failure.

        Args:
            withdrawal: Withdrawal transaction to execute
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.platform_private_key:
                logger.error("Platform wallet not configured")
                withdrawal.status = "failed"
                withdrawal.error_message = "Platform wallet not configured"
                await db.commit()
                return False

            withdrawal.status = "processing"
            await db.commit()

            logger.info(f"Executing withdrawal {withdrawal.id} via Uniswap V4 SDK...")

            import subprocess
            import json
            from pathlib import Path

            # Calculate AGNT amount after fee
            agnt_after_fee = withdrawal.agnt_amount_in - withdrawal.fee_agnt
            agnt_raw_amount = int(agnt_after_fee * Decimal(10 ** 18))  # AGNT has 18 decimals
            recipient = self.web3.to_checksum_address(withdrawal.recipient_address)

            logger.info(f"Swapping {agnt_after_fee} AGNT for USDC via Uniswap V4 SDK...")

            # Call the Node.js swap script using the official Uniswap V4 SDK
            project_root = Path(__file__).parent.parent.parent.parent
            swap_script = project_root / "scripts" / "swap_agnt_to_usdc.js"

            result = subprocess.run(
                [
                    "node", str(swap_script),
                    str(agnt_raw_amount),
                    recipient,
                    self.platform_private_key
                ],
                capture_output=True,
                text=True,
                timeout=180,
                cwd=str(project_root)
            )

            # Log stderr (progress messages)
            if result.stderr:
                for line in result.stderr.strip().split('\n'):
                    logger.info(f"[swap-sdk] {line}")

            # Parse stdout (JSON result)
            if not result.stdout.strip():
                raise Exception(f"Swap script produced no output. Exit code: {result.returncode}")

            swap_result = json.loads(result.stdout.strip())

            if not swap_result.get('success'):
                raise Exception(f"Uniswap swap failed: {swap_result.get('error', 'Unknown error')}")

            transfer_tx_hash = swap_result['txHash']
            usdc_amount = Decimal(swap_result['usdcAmount'])

            exchange_rate = usdc_amount / agnt_after_fee if agnt_after_fee > 0 else Decimal(0)

            logger.info(
                f"Uniswap swap executed: {agnt_after_fee} AGNT -> {usdc_amount} USDC "
                f"(tx: {transfer_tx_hash})"
            )

            # Update withdrawal record
            withdrawal.usdc_amount_out = usdc_amount
            withdrawal.exchange_rate = exchange_rate
            withdrawal.transfer_tx_hash = transfer_tx_hash
            withdrawal.status = "completed"
            withdrawal.completed_at = datetime.utcnow()
            withdrawal.error_message = None

            await db.commit()

            logger.info(f"Withdrawal {withdrawal.id} completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error executing withdrawal {withdrawal.id}: {e}", exc_info=True)

            # Refund AGNT to agent on failure
            try:
                result = await db.execute(
                    select(Agent).where(Agent.id == withdrawal.agent_id)
                )
                agent = result.scalar_one_or_none()
                if agent:
                    agent.balance += withdrawal.agnt_amount_in
                    agent.total_spent -= withdrawal.agnt_amount_in

                withdrawal.status = "failed"
                withdrawal.error_message = str(e)[:500]
                await db.commit()

                logger.info(f"Refunded {withdrawal.agnt_amount_in} AGNT to agent {withdrawal.agent_id}")
            except Exception as refund_error:
                logger.error(f"Error refunding withdrawal: {refund_error}", exc_info=True)

            return False


# Singleton instance
withdrawal_service = WithdrawalService()
