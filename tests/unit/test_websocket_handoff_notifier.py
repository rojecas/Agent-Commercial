"""
test_websocket_handoff_notifier.py — Tests unitarios para el notifier de WebSocket.
"""
import pytest
from unittest.mock import MagicMock
from src.core.handoff.websocket_handoff_notifier import WebSocketHandoffNotifier

@pytest.fixture
def notifier():
    return WebSocketHandoffNotifier()

@pytest.fixture
def mock_models():
    conversation = MagicMock()
    conversation.id = 123
    
    message = MagicMock()
    message.platform = "web"
    
    advisor = MagicMock()
    advisor.name = "Carlos Pérez"
    
    return conversation, message, advisor

@pytest.mark.asyncio
async def test_notify_available_retorna_mensaje_con_nombre_asesor(notifier, mock_models):
    # GIVEN
    conversation, message, advisor = mock_models
    summary = "El usuario quiere comprar balanzas."
    
    # WHEN
    result = await notifier.notify_available(conversation, message, advisor, summary)
    
    # THEN
    assert "Carlos Pérez" in result
    assert "conectar" in result.lower()
    assert "🤝" in result

@pytest.mark.asyncio
async def test_notify_unavailable_retorna_mensaje_esperado(notifier, mock_models):
    # GIVEN
    conversation, message, _ = mock_models
    summary = "El usuario tiene dudas técnicas."
    
    # WHEN
    result = await notifier.notify_unavailable(conversation, message, summary)
    
    # THEN
    assert "no tenemos asesores disponibles" in result.lower()
    assert "📋" in result
    assert "contacto" in result
