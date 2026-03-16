"""
Tests unitarios para WhatsAppHandoffNotifier — Issue #29.

Verifica que el notifier:
- Llama al whatsapp_responder con la ficha correcta (con y sin asesor)
- Retorna los mensajes correctos al cliente
- Maneja correctamente la falta de configuración
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.handoff.whatsapp_handoff_notifier import WhatsAppHandoffNotifier


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def notifier():
    return WhatsAppHandoffNotifier()


def make_conversation(conv_id=42):
    c = MagicMock()
    c.id = conv_id
    c.tenant_id = "inasc_001"
    return c


def make_message(platform="whatsapp", platform_user_id="573001234567", user_name="Juan Pérez"):
    m = MagicMock()
    m.platform = platform
    m.platform_user_id = platform_user_id
    m.user_name = user_name
    m.tenant_id = "inasc_001"
    return m


def make_advisor(name="Ana Gómez", whatsapp="+573009998877"):
    a = MagicMock()
    a.name = name
    a.whatsapp_number = whatsapp
    return a


# ── Tests notify_available ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_whatsapp_notify_available_calls_responder(notifier):
    """Verifica que llama a send_message del responder con los datos del asesor."""
    conversation = make_conversation()
    message = make_message()
    advisor = make_advisor()

    with patch("src.core.handoff.whatsapp_handoff_notifier.whatsapp_responder") as mock_ws:
        mock_ws.send_message = AsyncMock(return_value=True)

        await notifier.notify_available(
            conversation, message, advisor, "Solicitud de catálogo técnico"
        )

    mock_ws.send_message.assert_awaited_once()
    dest, text = mock_ws.send_message.call_args.args
    assert dest == advisor.whatsapp_number
    assert "Ana Gómez" in text
    assert "Juan Pérez" in text
    assert "Solicitud de catálogo técnico" in text


@pytest.mark.asyncio
async def test_whatsapp_notify_available_returns_client_message(notifier):
    """El mensaje devuelto al cliente confirma la transferencia al asesor."""
    conversation = make_conversation()
    message = make_message()
    advisor = make_advisor(name="Carlos Ruiz")

    with patch("src.core.handoff.whatsapp_handoff_notifier.whatsapp_responder") as mock_ws:
        mock_ws.send_message = AsyncMock(return_value=True)
        result = await notifier.notify_available(conversation, message, advisor, "resumen")

    assert "Carlos Ruiz" in result
    assert "conectando" in result.lower()


# ── Tests notify_unavailable ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_whatsapp_notify_unavailable_calls_support(notifier):
    """Verifica que llama al número de soporte cuando no hay asesor."""
    conversation = make_conversation()
    message = make_message()
    support_num = "573000000000"

    with patch("src.core.handoff.whatsapp_handoff_notifier.whatsapp_responder") as mock_ws, \
         patch("src.core.handoff.whatsapp_handoff_notifier.WHATSAPP_SUPPORT_NUMBER", support_num):
        mock_ws.send_message = AsyncMock(return_value=True)

        await notifier.notify_unavailable(conversation, message, "Caso urgente")

    mock_ws.send_message.assert_awaited_once()
    dest, text = mock_ws.send_message.call_args.args
    assert dest == support_num
    assert "URGENTE" in text.upper()
    assert "PENDIENTE" in text.upper()


@pytest.mark.asyncio
async def test_whatsapp_notify_unavailable_returns_client_message(notifier):
    """El mensaje devuelto informa que habrá un contacto posterior."""
    conversation = make_conversation()
    message = make_message()

    with patch("src.core.handoff.whatsapp_handoff_notifier.whatsapp_responder") as mock_ws:
        mock_ws.send_message = AsyncMock(return_value=True)
        result = await notifier.notify_unavailable(conversation, message, "resumen")

    assert "no tenemos asesores disponibles" in result.lower()
    assert "muy pronto" in result.lower()


# ── Error Handling ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_whatsapp_no_numbers_configured_no_exception(notifier):
    """No debe explotar si no hay números configurados."""
    conversation = make_conversation()
    message = make_message()
    advisor = make_advisor(whatsapp=None)

    with patch("src.core.handoff.whatsapp_handoff_notifier.whatsapp_responder") as mock_ws, \
         patch("src.core.handoff.whatsapp_handoff_notifier.WHATSAPP_SUPPORT_NUMBER", ""):
        
        # Disponible pero asesor sin número
        res1 = await notifier.notify_available(conversation, message, advisor, "resumen")
        # No disponible y soporte sin número
        res2 = await notifier.notify_unavailable(conversation, message, "resumen")

    assert mock_ws.send_message.call_count == 0
    assert isinstance(res1, str)
    assert isinstance(res2, str)
