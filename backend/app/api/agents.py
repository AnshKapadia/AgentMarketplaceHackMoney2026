"""Agents API router."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_agent, get_optional_agent
from app.models.agent import Agent
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentPublic,
    AgentResponse,
    AgentRegisterResponse,
)
from app.services.agent_service import (
    create_agent,
    search_agents,
    update_agent,
    get_agent_by_id,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=AgentRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new agent (public endpoint).

    Returns the API key ONLY ONCE - save it securely!
    """
    try:
        # Resolve ENS name in wallet_address if provided
        ens_name = None
        ens_verified = False
        wallet_address = agent_data.wallet_address

        try:
            from app.config import settings
            if settings.ENS_ENABLED and wallet_address:
                from app.services.ens_service import ens_service

                # If wallet_address is an ENS name, resolve it
                if '.' in wallet_address and not wallet_address.startswith('0x'):
                    ens_name = wallet_address
                    resolved = await ens_service.resolve_name(wallet_address)
                    if resolved:
                        agent_data.wallet_address = resolved
                        # Verify ownership (name resolves to this address)
                        ens_verified = True
                        logger.info(f"Resolved ENS name {ens_name} -> {resolved}")
                    else:
                        logger.warning(f"Could not resolve ENS name: {wallet_address}")
                        # Keep original value, don't block registration
                else:
                    # wallet_address is a hex address — try reverse resolution
                    reverse_name = await ens_service.resolve_address(wallet_address)
                    if reverse_name:
                        ens_name = reverse_name
                        ens_verified = True
                        logger.info(f"Reverse ENS lookup: {wallet_address} -> {reverse_name}")
        except Exception as ens_error:
            logger.warning(f"ENS resolution failed (non-critical): {ens_error}")

        agent, api_key = await create_agent(db, agent_data)

        # Set ENS fields if resolved
        if ens_name:
            agent.ens_name = ens_name
            agent.ens_verified = ens_verified
            await db.commit()

        return AgentRegisterResponse(
            agent_id=agent.id,
            name=agent.name,
            api_key=api_key,
            ens_name=ens_name,
            ens_verified=ens_verified,
            created_at=agent.created_at
        )
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "DUPLICATE_AGENT_NAME",
                    "message": f"Agent with name '{agent_data.name}' already exists"
                }
            )
        raise


@router.get("", response_model=List[AgentPublic])
async def list_agents(
    q: Optional[str] = Query(None, description="Search query (name, description)"),
    capabilities: Optional[str] = Query(None, description="Comma-separated capabilities"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    min_reputation: Optional[float] = Query(None, description="Minimum reputation score"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_agent: Optional[Agent] = Depends(get_optional_agent)
):
    """
    Search and browse agents (public endpoint with optional auth).
    """
    # Parse capabilities
    caps_list = None
    if capabilities:
        caps_list = [c.strip() for c in capabilities.split(",")]

    agents = await search_agents(
        db=db,
        query_text=q,
        capabilities=caps_list,
        status=status_filter,
        min_reputation=min_reputation,
        limit=limit,
        offset=offset
    )

    return agents


@router.get("/me", response_model=AgentResponse)
async def get_current_agent_profile(
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current authenticated agent's profile with AGNT and USD balances.
    """
    from app.config import settings

    # Convert to response model
    agent_response = AgentResponse.model_validate(current_agent)

    # Calculate USD equivalents
    conversion_rate = settings.USDC_TO_AGNT_RATE
    agent_response.balance_usd = current_agent.balance / conversion_rate
    agent_response.total_earned_usd = current_agent.total_earned / conversion_rate
    agent_response.total_spent_usd = current_agent.total_spent / conversion_rate

    # Set currency
    agent_response.balance_currency = "AGNT"

    return agent_response


@router.get("/{agent_id}", response_model=AgentPublic)
async def get_agent_profile(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific agent's public profile.
    """
    agent = await get_agent_by_id(db, agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "AGENT_NOT_FOUND",
                "message": f"Agent with ID {agent_id} not found"
            }
        )

    return agent


@router.patch("/me", response_model=AgentResponse)
async def update_current_agent(
    updates: AgentUpdate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current agent's profile.
    """
    try:
        updated_agent = await update_agent(db, str(current_agent.id), updates)
        return updated_agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "AGENT_NOT_FOUND",
                "message": str(e)
            }
        )


@router.put("/me/status", response_model=AgentResponse)
async def update_agent_status(
    status_update: AgentUpdate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current agent's status.
    """
    if not status_update.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_STATUS",
                "message": "Status is required"
            }
        )

    try:
        updated_agent = await update_agent(db, str(current_agent.id), status_update)
        return updated_agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "AGENT_NOT_FOUND",
                "message": str(e)
            }
        )
