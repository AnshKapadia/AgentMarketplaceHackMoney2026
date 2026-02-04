import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from app.services.agent_service import search_agents
from app.services.chain_service import ChainService

@pytest.mark.asyncio
async def test_search_agents_multi_term(db, client_agent):
    # client_agent has name="TestClient" and description="Test client agent"
    
    # "Test" AND "Client" should match
    results = await search_agents(db, query_text="Test Client")
    assert len(results) >= 1
    
    # "Client" AND "Agent" should match
    results = await search_agents(db, query_text="Client Agent")
    assert len(results) >= 1
    
    # "Test" AND "Zebra" should NOT match
    results = await search_agents(db, query_text="Test Zebra")
    assert len(results) == 0

def test_chain_service_verification_logic():
    # Mock Web3
    mock_web3 = MagicMock()
    
    # Service instance with mocked web3
    service = ChainService()
    service.web3 = mock_web3
    
    # Mock receipt
    mock_receipt = {'status': 1}
    mock_web3.eth.get_transaction_receipt.return_value = mock_receipt
    
    # Mock Contract
    mock_contract = MagicMock()
    mock_web3.eth.contract.return_value = mock_contract
    
    # Mock Decimals
    mock_contract.functions.decimals.return_value.call.return_value = 6
    
    # Mock Events
    # event['args']['to'] = recipient
    # event['args']['value'] = amount * 10^6
    recipient = "0x1234567890123456789012345678901234567890"
    amount = Decimal("10.5")
    
    mock_event = {
        'args': {
            'to': recipient,
            'value': int(amount * 1000000)
        }
    }
    
    # Mock processing logs
    mock_contract.events.Transfer.return_value.process_receipt.return_value = [mock_event]
    
    # Test valid
    is_valid = service.verify_transaction(
        tx_hash="0xabc",
        expected_amount=amount,
        recipient_address=recipient
    )
    assert is_valid is True
    
    # Test invalid recipient
    is_valid = service.verify_transaction(
        tx_hash="0xabc",
        expected_amount=amount,
        recipient_address="0x9999999999999999999999999999999999999999"
    )
    assert is_valid is False

    # Test invalid amount
    is_valid = service.verify_transaction(
        tx_hash="0xabc",
        expected_amount=Decimal("20.0"),
        recipient_address=recipient
    )
    assert is_valid is False
