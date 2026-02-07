"""ENS resolution and verification service for Ethereum Sepolia."""

import logging
from typing import Optional

from web3 import Web3

from app.config import settings

logger = logging.getLogger(__name__)


# Minimal ABIs for ENS resolution
ENS_REGISTRY_ABI = [
    {
        "inputs": [{"name": "node", "type": "bytes32"}],
        "name": "resolver",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "node", "type": "bytes32"}],
        "name": "owner",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
]

ENS_RESOLVER_ABI = [
    {
        "inputs": [{"name": "node", "type": "bytes32"}],
        "name": "addr",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "node", "type": "bytes32"}],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
]


class ENSService:
    """Service for ENS name resolution and agent verification."""

    def __init__(self):
        self.enabled = False

        if not settings.ENS_ENABLED:
            logger.info("ENS integration disabled (ENS_ENABLED=false)")
            return

        try:
            self.web3 = Web3(Web3.HTTPProvider(settings.ETH_SEPOLIA_RPC_URL))

            if not self.web3.is_connected():
                logger.warning("ENS integration disabled: cannot connect to Ethereum Sepolia RPC")
                return

            self.registry = self.web3.eth.contract(
                address=Web3.to_checksum_address(settings.ENS_REGISTRY_ADDRESS),
                abi=ENS_REGISTRY_ABI
            )

            self.enabled = True
            logger.info("ENS integration enabled (resolution + verification)")
        except Exception as e:
            logger.error(f"ENS integration init failed: {e}", exc_info=True)
            self.enabled = False

    def _namehash(self, name: str) -> bytes:
        """Compute EIP-137 namehash."""
        node = b'\x00' * 32
        if not name:
            return node

        labels = name.split('.')
        for label in reversed(labels):
            label_hash = Web3.keccak(text=label)
            node = Web3.keccak(node + label_hash)

        return node

    async def resolve_name(self, name: str) -> Optional[str]:
        """
        Forward resolution: ENS name -> address.

        Args:
            name: ENS name (e.g. "vitalik.eth")

        Returns:
            Checksummed address or None if not found
        """
        if not self.enabled:
            logger.debug("ENS not enabled, cannot resolve")
            return None

        try:
            node = self._namehash(name)

            # Get the resolver for this name
            resolver_addr = self.registry.functions.resolver(node).call()

            if resolver_addr == "0x0000000000000000000000000000000000000000":
                logger.debug(f"No resolver set for {name}")
                return None

            # Query the resolver for the address
            resolver = self.web3.eth.contract(
                address=resolver_addr,
                abi=ENS_RESOLVER_ABI
            )

            addr = resolver.functions.addr(node).call()

            if addr == "0x0000000000000000000000000000000000000000":
                logger.debug(f"No address record for {name}")
                return None

            resolved = Web3.to_checksum_address(addr)
            logger.info(f"ENS resolved: {name} -> {resolved}")
            return resolved

        except Exception as e:
            logger.warning(f"ENS resolution failed for {name}: {e}")
            return None

    async def resolve_address(self, address: str) -> Optional[str]:
        """
        Reverse resolution: address -> ENS name.

        Uses the reverse registrar: <addr>.addr.reverse

        Args:
            address: Ethereum address (checksummed or not)

        Returns:
            ENS name or None if no reverse record
        """
        if not self.enabled:
            return None

        try:
            addr_lower = address.lower().replace("0x", "")
            reverse_name = f"{addr_lower}.addr.reverse"
            node = self._namehash(reverse_name)

            # Get the resolver for the reverse record
            resolver_addr = self.registry.functions.resolver(node).call()

            if resolver_addr == "0x0000000000000000000000000000000000000000":
                logger.debug(f"No reverse resolver for {address}")
                return None

            resolver = self.web3.eth.contract(
                address=resolver_addr,
                abi=ENS_RESOLVER_ABI
            )

            name = resolver.functions.name(node).call()

            if not name:
                return None

            # Verify forward resolution matches (prevents spoofing)
            forward_addr = await self.resolve_name(name)
            if forward_addr and forward_addr.lower() == address.lower():
                logger.info(f"ENS reverse resolved: {address} -> {name}")
                return name
            else:
                logger.warning(
                    f"ENS reverse record for {address} points to {name}, "
                    f"but forward resolution gives {forward_addr} (mismatch)"
                )
                return None

        except Exception as e:
            logger.warning(f"ENS reverse resolution failed for {address}: {e}")
            return None

    async def verify_ens_ownership(self, address: str, claimed_name: str) -> bool:
        """
        Verify that an address owns a claimed ENS name.

        Checks that the ENS name resolves to the given address.

        Args:
            address: The wallet address claiming ownership
            claimed_name: The ENS name being claimed

        Returns:
            True if the name resolves to the address
        """
        if not self.enabled:
            return False

        try:
            resolved_addr = await self.resolve_name(claimed_name)
            if not resolved_addr:
                return False

            match = resolved_addr.lower() == address.lower()
            if match:
                logger.info(f"ENS ownership verified: {claimed_name} -> {address}")
            else:
                logger.info(
                    f"ENS ownership NOT verified: {claimed_name} resolves to "
                    f"{resolved_addr}, not {address}"
                )
            return match

        except Exception as e:
            logger.warning(f"ENS ownership verification failed: {e}")
            return False

    async def resolve_or_passthrough(self, input_str: str) -> str:
        """
        Accept either an ENS name or an address. If it's an ENS name,
        resolve it to an address. Otherwise return as-is.

        Args:
            input_str: ENS name (e.g. "vitalik.eth") or hex address

        Returns:
            Checksummed Ethereum address

        Raises:
            ValueError: If ENS name cannot be resolved or address is invalid
        """
        # If it looks like an ENS name (contains a dot and doesn't start with 0x)
        if '.' in input_str and not input_str.startswith('0x'):
            resolved = await self.resolve_name(input_str)
            if not resolved:
                raise ValueError(f"Could not resolve ENS name: {input_str}")
            return resolved

        # Otherwise treat as address
        if not Web3.is_address(input_str):
            raise ValueError(f"Invalid address or ENS name: {input_str}")

        return Web3.to_checksum_address(input_str)


# Singleton instance
ens_service = ENSService()
