import pytest
from unittest.mock import AsyncMock, MagicMock
from src.database import crud

@pytest.mark.asyncio
async def test_get_handed_off_conversations_mock():
    """Test unitario básico de la función CRUD sin depender de FastAPI."""
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars().unique().all.return_value = []
    session.execute.return_value = mock_result
    
    res = await crud.get_handed_off_conversations(session, "tenant_test")
    assert isinstance(res, list)
    session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_conversation_messages_mock():
    """Test unitario de la función CRUD de mensajes."""
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = []
    session.execute.return_value = mock_result
    
    res = await crud.get_conversation_messages(session, 1, "tenant_test")
    assert isinstance(res, list)
    session.execute.assert_called_once()
