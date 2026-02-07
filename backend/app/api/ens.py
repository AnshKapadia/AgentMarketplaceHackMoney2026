"""ENS resolution API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.services.ens_service import ens_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ens", tags=["ens"])


class ENSResolveResponse(BaseModel):
    name: str
    address: Optional[str] = None
    resolved: bool = False


class ENSReverseResponse(BaseModel):
    address: str
    name: Optional[str] = None
    resolved: bool = False


@router.get("/resolve/{name:path}", response_model=ENSResolveResponse)
async def resolve_ens_name(name: str):
    """
    Resolve an ENS name to an Ethereum address.

    Example: /api/ens/resolve/vitalik.eth
    """
    if not ens_service.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ENS resolution service is not available"
        )

    address = await ens_service.resolve_name(name)

    return ENSResolveResponse(
        name=name,
        address=address,
        resolved=address is not None
    )


@router.get("/reverse/{address}", response_model=ENSReverseResponse)
async def reverse_resolve_address(address: str):
    """
    Reverse-resolve an Ethereum address to an ENS name.

    Example: /api/ens/reverse/0xd8dA6BF26964aF9D68eC213aE187C76C3bdd5f6e
    """
    if not ens_service.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ENS resolution service is not available"
        )

    ens_name = await ens_service.resolve_address(address)

    return ENSReverseResponse(
        address=address,
        name=ens_name,
        resolved=ens_name is not None
    )
