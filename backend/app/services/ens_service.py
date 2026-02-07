"""ENS subdomain registration service for agent identities on Ethereum Sepolia."""

import re
import json
import logging
from typing import Dict, List, Optional

from web3 import Web3

from app.config import settings

logger = logging.getLogger(__name__)


# Minimal ABIs for ENS contracts
ENS_REGISTRY_ABI = [
    {
        "inputs": [
            {"name": "node", "type": "bytes32"},
            {"name": "label", "type": "bytes32"},
            {"name": "owner", "type": "address"},
            {"name": "resolver", "type": "address"},
            {"name": "ttl", "type": "uint64"}
        ],
        "name": "setSubnodeRecord",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "node", "type": "bytes32"}
        ],
        "name": "owner",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

ENS_RESOLVER_ABI = [
    {
        "inputs": [
            {"name": "node", "type": "bytes32"},
            {"name": "key", "type": "string"},
            {"name": "value", "type": "string"}
        ],
        "name": "setText",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "node", "type": "bytes32"},
            {"name": "addr", "type": "address"}
        ],
        "name": "setAddr",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


class ENSService:
    """Service for registering ENS subdomains for agents."""

    def __init__(self):
        self.enabled = False

        if not settings.ENS_ENABLED:
            logger.info("ENS integration disabled (ENS_ENABLED=false)")
            return

        if not settings.ENS_PARENT_DOMAIN:
            logger.warning("ENS integration disabled: ENS_PARENT_DOMAIN not set")
            return

        if not settings.DEPLOYER_PRIVATE_KEY:
            logger.warning("ENS integration disabled: DEPLOYER_PRIVATE_KEY not set")
            return

        try:
            self.web3 = Web3(Web3.HTTPProvider(settings.ETH_SEPOLIA_RPC_URL))

            if not self.web3.is_connected():
                logger.warning("ENS integration disabled: cannot connect to Ethereum Sepolia RPC")
                return

            self.account = self.web3.eth.account.from_key(settings.DEPLOYER_PRIVATE_KEY)
            self.platform_address = self.account.address

            self.parent_domain = settings.ENS_PARENT_DOMAIN
            self.parent_node = self._namehash(self.parent_domain)

            self.registry = self.web3.eth.contract(
                address=Web3.to_checksum_address(settings.ENS_REGISTRY_ADDRESS),
                abi=ENS_REGISTRY_ABI
            )
            self.resolver = self.web3.eth.contract(
                address=Web3.to_checksum_address(settings.ENS_RESOLVER_ADDRESS),
                abi=ENS_RESOLVER_ABI
            )
            self.resolver_address = Web3.to_checksum_address(settings.ENS_RESOLVER_ADDRESS)

            self.enabled = True
            logger.info(
                f"ENS integration enabled: parent={self.parent_domain}, "
                f"platform={self.platform_address}"
            )
        except Exception as e:
            logger.error(f"ENS integration init failed: {e}", exc_info=True)
            self.enabled = False

    def _namehash(self, name: str) -> bytes:
        """
        Compute EIP-137 namehash.

        namehash('') = 0x00...00
        namehash('eth') = keccak256(namehash('') + keccak256('eth'))
        namehash('foo.eth') = keccak256(namehash('eth') + keccak256('foo'))
        """
        node = b'\x00' * 32
        if not name:
            return node

        labels = name.split('.')
        for label in reversed(labels):
            label_hash = Web3.keccak(text=label)
            node = Web3.keccak(node + label_hash)

        return node

    def _sanitize_label(self, name: str) -> str:
        """
        Sanitize agent name into a valid ENS label.

        "Security Reviewer" -> "security-reviewer"
        "Alice's Bot #1" -> "alices-bot-1"
        """
        label = name.lower()
        label = label.replace(' ', '-')
        label = re.sub(r'[^a-z0-9\-]', '', label)
        label = re.sub(r'-+', '-', label)
        label = label.strip('-')

        if not label:
            label = 'agent'

        return label

    async def create_subdomain(
        self,
        agent_name: str,
        wallet_address: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Register an ENS subdomain for an agent.

        Creates: <sanitized-name>.<parent_domain>
        Sets text records for agent metadata.

        Args:
            agent_name: Display name of the agent
            wallet_address: Optional wallet address to set as addr record
            metadata: Dict with keys like 'agent_id', 'description', 'capabilities'

        Returns:
            Dict with 'ens_name' and 'tx_hashes', or None on failure
        """
        if not self.enabled:
            logger.debug("ENS not enabled, skipping subdomain creation")
            return None

        metadata = metadata or {}
        label = self._sanitize_label(agent_name)
        subdomain = f"{label}.{self.parent_domain}"
        subdomain_node = self._namehash(subdomain)
        label_hash = Web3.keccak(text=label)

        logger.info(f"Creating ENS subdomain: {subdomain}")

        tx_hashes = []

        try:
            # Fetch nonce once, increment locally
            nonce = self.web3.eth.get_transaction_count(self.platform_address)
            gas_price = self.web3.eth.gas_price

            # TX 1: setSubnodeRecord on Registry
            tx1 = self.registry.functions.setSubnodeRecord(
                self.parent_node,
                label_hash,
                self.platform_address,
                self.resolver_address,
                0  # TTL
            ).build_transaction({
                'from': self.platform_address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': gas_price,
                'chainId': 11155111
            })

            signed_tx1 = self.account.sign_transaction(tx1)
            tx1_hash = self.web3.eth.send_raw_transaction(signed_tx1.raw_transaction)
            tx_hashes.append(tx1_hash.hex())
            logger.info(f"setSubnodeRecord tx: {tx1_hash.hex()}")

            # Wait for TX 1 before proceeding
            receipt1 = self.web3.eth.wait_for_transaction_receipt(tx1_hash, timeout=120)
            if receipt1['status'] != 1:
                logger.error(f"setSubnodeRecord failed: {tx1_hash.hex()}")
                return None

            nonce += 1

            # TX 2: setAddr on Resolver (if wallet provided)
            if wallet_address:
                try:
                    tx2 = self.resolver.functions.setAddr(
                        subdomain_node,
                        Web3.to_checksum_address(wallet_address)
                    ).build_transaction({
                        'from': self.platform_address,
                        'nonce': nonce,
                        'gas': 100000,
                        'gasPrice': gas_price,
                        'chainId': 11155111
                    })

                    signed_tx2 = self.account.sign_transaction(tx2)
                    tx2_hash = self.web3.eth.send_raw_transaction(signed_tx2.raw_transaction)
                    tx_hashes.append(tx2_hash.hex())
                    logger.info(f"setAddr tx: {tx2_hash.hex()}")

                    receipt2 = self.web3.eth.wait_for_transaction_receipt(tx2_hash, timeout=120)
                    if receipt2['status'] != 1:
                        logger.warning(f"setAddr failed (non-critical): {tx2_hash.hex()}")

                    nonce += 1
                except Exception as e:
                    logger.warning(f"setAddr failed (non-critical): {e}")
                    nonce += 1

            # TX 3+: setText records on Resolver
            text_records = {}

            if metadata.get('agent_id'):
                text_records['com.agentmarket.id'] = metadata['agent_id']

            if agent_name:
                text_records['com.agentmarket.name'] = agent_name

            if metadata.get('description'):
                text_records['description'] = metadata['description']

            if metadata.get('capabilities'):
                text_records['com.agentmarket.capabilities'] = json.dumps(metadata['capabilities'])

            for key, value in text_records.items():
                try:
                    tx = self.resolver.functions.setText(
                        subdomain_node,
                        key,
                        value
                    ).build_transaction({
                        'from': self.platform_address,
                        'nonce': nonce,
                        'gas': 100000,
                        'gasPrice': gas_price,
                        'chainId': 11155111
                    })

                    signed_tx = self.account.sign_transaction(tx)
                    tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    tx_hashes.append(tx_hash.hex())
                    logger.info(f"setText({key}) tx: {tx_hash.hex()}")

                    receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    if receipt['status'] != 1:
                        logger.warning(f"setText({key}) failed (non-critical): {tx_hash.hex()}")

                    nonce += 1
                except Exception as e:
                    logger.warning(f"setText({key}) failed (non-critical): {e}")
                    nonce += 1

            logger.info(f"ENS subdomain created: {subdomain} ({len(tx_hashes)} txs)")

            return {
                'ens_name': subdomain,
                'tx_hashes': tx_hashes
            }

        except Exception as e:
            logger.error(f"ENS subdomain creation failed for {agent_name}: {e}", exc_info=True)
            return None


# Singleton instance
ens_service = ENSService()
