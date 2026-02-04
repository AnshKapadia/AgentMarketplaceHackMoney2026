"""Chain service for interacting with blockchain networks."""

import os
from decimal import Decimal
from typing import Optional
from web3 import Web3
from web3.exceptions import TransactionNotFound

class ChainService:
    def __init__(self):
        self.rpc_url = os.getenv("WEB3_RPC_URL", "https://sepolia.base.org")
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.usdc_address = os.getenv("USDC_ADDRESS", "0x036CbD53842c5426634e7929541eC2318f3dCF7e") # Base Sepolia USDC
        
        # Reduced ABI for Transfer events and decimals
        self.erc20_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "from", "type": "address"},
                    {"indexed": True, "name": "to", "type": "address"},
                    {"indexed": False, "name": "value", "type": "uint256"}
                ],
                "name": "Transfer",
                "type": "event"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
    def verify_transaction(
        self, 
        tx_hash: str, 
        expected_amount: Decimal, 
        recipient_address: str,
        token_address: Optional[str] = None
    ) -> bool:
        """
        Verify a transaction on chain.
        
        Args:
            tx_hash: Transaction hash string
            expected_amount: Expected amount (in human readable units, e.g. 10.5 USDC)
            recipient_address: Expected recipient wallet address
            token_address: Optional token contract address (defaults to USDC env var)
            
        Returns:
            True if valid and confirmed
        """
        try:
            # 1. Get Transaction Receipt
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            
            if not receipt:
                return False
                
            if receipt['status'] != 1:
                return False  # Transaction failed
                
            # 2. Check for Token Transfer
            target_token = token_address or self.usdc_address
            contract = self.web3.eth.contract(address=target_token, abi=self.erc20_abi)
            
            # Parse logs for Transfer events
            transfers = contract.events.Transfer().process_receipt(receipt)
            
            for event in transfers:
                args = event['args']
                
                # Check recipient
                if args['to'].lower() != recipient_address.lower():
                    continue
                    
                # Check amount
                # We need decimals to convert
                decimals = contract.functions.decimals().call()
                amount_wei = args['value']
                amount_human = Decimal(amount_wei) / Decimal(10 ** decimals)
                
                # Allow small implementation diff (epsilon) if needed, but exact match preferred
                if amount_human == expected_amount:
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Error verifying transaction: {e}")
            return False

# Singleton instance
chain_service = ChainService()
