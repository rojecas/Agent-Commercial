"""
Tests unitarios para TelegramHandoffNotifier — Issue #24.

Verifica que el notifier:
- Envía sendMessage a TELEGRAM_ADVISOR_GROUP_ID (con y sin asesor)
- Retorna los mensajes correctos al cliente
- No lanza excepciones si las variables de entorno no están configuradas
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.handoff.telegram_handoff_notifier import TelegramHandoffNotifier


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def notifier():
    return TelegramHandoffNotifier()


def make_conversation(conv_id=42):
    c = MagicMock()
    c.id = conv_id
    return c


def make_message(platform="telegram", platform_user_id="123456789"):
    m = MagicMock()
    m.platform = platform
    m.platform_user_id = platform_user_id
    return m


def make_advisor(name="Ana Gómez"):
    a = MagicMock()
    a.name = name
    return a


# ── Tests notify_available ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_available_llama_telegram_api(notifier):
    """Verifica que se llama a sendMessage de la API de Telegram con los datos del caso."""
    conversation = make_conversation()
    message = make_message()
    advisor = make_advisor()

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch(
        "src.core.handoff.telegram_handoff_notifier.TELEGRAM_BOT_TOKEN", "fake_token"
    ), patch(
        "src.core.handoff.telegram_handoff_notifier.TELEGRAM_ADVISOR_GROUP_ID", "-100123456"
    ), patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        await notifier.notify_available(conversation, message, advisor, "El cliente necesita filtros FX-200")

    mock_client.post.assert_awaited_once()
    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs["json"]
    assert payload["chat_id"] == "-100123456"
    assert "Ana Gómez" in payload["text"]
    assert "123456789" in payload["text"]


@pytest.mark.asyncio
async def test_notify_available_retorna_mensaje_cliente(notifier):
    """El mensaje devuelto al cliente menciona al asesor asignado."""
    conversation = make_conversation()
    message = make_message()
    advisor = make_advisor("Carlos Pérez")

    with patch("src.core.handoff.telegram_handoff_notifier.TELEGRAM_BOT_TOKEN", "t"), \
         patch("src.core.handoff.telegram_handoff_notifier.TELEGRAM_ADVISOR_GROUP_ID", "-1"), \
         patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
        mock_client_class.return_value = mock_client

        result = await notifier.notify_available(conversation, message, advisor, "resumen")

    assert "Carlos Pérez" in result


# ── Tests notify_unavailable ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_unavailable_llama_telegram_api(notifier):
    """Verifica que sendMessage es llamado al grupo cuando no hay asesor."""
    conversation = make_conversation()
    message = make_message()

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("src.core.handoff.telegram_handoff_notifier.TELEGRAM_BOT_TOKEN", "fake"), \
         patch("src.core.handoff.telegram_handoff_notifier.TELEGRAM_ADVISOR_GROUP_ID", "-100999"), \
         patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        await notifier.notify_unavailable(conversation, message, "Caso de filtración compleja")

    mock_client.post.assert_awaited_once()
    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["chat_id"] == "-100999"
    assert "Pendiente" in payload["text"] or "pendiente" in payload["text"].lower()


@pytest.mark.asyncio
async def test_notify_unavailable_retorna_mensaje_cliente(notifier):
    """El mensaje devuelto informa que un asesor hará callback."""
    conversation = make_conversation()
    message = make_message()

    with patch("src.core.handoff.telegram_handoff_notifier.TELEGRAM_BOT_TOKEN", "t"), \
         patch("src.core.handoff.telegram_handoff_notifier.TELEGRAM_ADVISOR_GROUP_ID", "-1"), \
         patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
        mock_client_class.return_value = mock_client

        result = await notifier.notify_unavailable(conversation, message, "resumen")

    assert len(result) > 0
    # Verifica que informa al cliente que habrá un callback
    assert any(word in result.lower() for word in ["contacto", "asesor", "pronto", "callback"])


# ── Test modo degradado ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sin_group_id_no_lanza_excepcion(notifier):
    """Si TELEGRAM_ADVISOR_GROUP_ID no está configurado, no lanza excepción."""
    conversation = make_conversation()
    message = make_message()
    advisor = make_advisor()

    with patch("src.core.handoff.telegram_handoff_notifier.TELEGRAM_BOT_TOKEN", ""), \
         patch("src.core.handoff.telegram_handoff_notifier.TELEGRAM_ADVISOR_GROUP_ID", ""):
        # No debe lanzar excepción — solo loguea warning
        result = await notifier.notify_available(conversation, message, advisor, "resumen")

    assert isinstance(result, str)
    assert len(result) > 0
