import pytest
from decimal import Decimal
from app.services.agent_service import update_balance, search_agents
from app.services.payment_service import payment_service
from app.models.agent import Agent

@pytest.mark.asyncio
async def test_update_balance(db, client_agent):
    agent_data, _ = client_agent
    agent_id = agent_data["id"]
    
    # Add funds
    agent = await update_balance(db, agent_id, Decimal("100.50"))
    assert agent.balance == Decimal("100.50")
    assert agent.total_earned == Decimal("100.50")
    
    # Spend funds
    agent = await update_balance(db, agent_id, Decimal("-50.25"))
    assert agent.balance == Decimal("50.25")
    assert agent.total_spent == Decimal("50.25")

@pytest.mark.asyncio
async def test_search_agents_query(db, client_agent):
    # client_agent has name="TestClient" and description="Test client agent"
    
    # Search by partial name (case insensitive)
    results = await search_agents(db, query_text="Client")
    assert len(results) >= 1
    found = False
    for a in results:
        if a.name == "TestClient":
            found = True
            break
    assert found
    
    # Search by partial description
    results = await search_agents(db, query_text="test client")
    found = False
    for a in results:
        if a.name == "TestClient":
            found = True
            break
    assert found
    
    # Search for non-existent
    results = await search_agents(db, query_text="NONEXISTENT_XYZ")
    assert len(results) == 0

@pytest.mark.asyncio
async def test_payment_metadata():
    meta = payment_service.generate_payment_metadata(
        amount=Decimal("10.00"),
        currency="USDC"
    )
    assert meta["x402-price"] == "10.00"
    assert meta["x402-currency"] == "USDC"
    assert "x402-recipient" in meta
    assert "x402-expiration" in meta

@pytest.mark.asyncio
async def test_verify_payment_endpoint(client, client_agent):
    agent_data, api_key = client_agent
    headers = {"X-Agent-Key": api_key}
    
    # Verify payment
    payload = {
        "tx_hash": "0x1234567890abcdef",
        "amount": 50.00,
        "recipient_agent_id": agent_data["id"] 
    }
    
    response = await client.post("/api/payments/verify", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Initial 0 + 50 = 50
    assert data["new_balance"] == 50.0
