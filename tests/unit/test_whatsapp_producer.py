"""
Tests unitarios para WhatsAppProducer.

Estructura idéntica a test_telegram_producer.py para consistencia.
No se necesita servidor real ni credenciales de Meta.
"""
import pytest
from unittest.mock import AsyncMock, patch
from src.core.producers.whatsapp_producer import WhatsAppProducer


# ── Helpers ────────────────────────────────────────────────────────

def _make_payload(
    phone: str = "573001234567",
    text: str = "Hola, ¿qué productos tienen?",
    name: str | None = "Juan Pérez",
    msg_type: str = "text",
) -> dict:
    """Construye un payload de Meta Cloud API mínimo pero válido."""
    message: dict = {"from": phone, "type": msg_type}
    if msg_type == "text":
        message["text"] = {"body": text}

    contacts = [{"profile": {"name": name}}] if name else []

    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [message],
                    "contacts": contacts,
                }
            }]
        }]
    }


# ── Tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_payload_campos_completos():
    """El producer extrae correctamente todos los campos del payload de Meta."""
    producer = WhatsAppProducer(tenant_id="inasc_001")
    payload = _make_payload(
        phone="573001234567",
        text="Necesito calibrar un equipo.",
        name="Ana Gómez",
    )
    msg = await producer.process_payload(payload)

    assert msg.platform == "whatsapp"
    assert msg.platform_user_id == "573001234567"
    assert msg.content == "Necesito calibrar un equipo."
    assert msg.user_name == "Ana Gómez"
    assert msg.tenant_id == "inasc_001"


@pytest.mark.asyncio
async def test_process_payload_sin_nombre_contacto():
    """El campo user_name es None cuando Meta no envía datos de contacto."""
    producer = WhatsAppProducer(tenant_id="inasc_001")
    payload = _make_payload(phone="573009876543", text="¿Tienen balanzas?", name=None)
    msg = await producer.process_payload(payload)

    assert msg.platform_user_id == "573009876543"
    assert msg.user_name is None
    assert msg.content == "¿Tienen balanzas?"


@pytest.mark.asyncio
async def test_process_payload_tenant_id_inyectado_por_productor():
    """El tenant_id viene del servidor, NUNCA del payload de Meta."""
    producer = WhatsAppProducer(tenant_id="inasc_tenant_test")
    payload = _make_payload()
    msg = await producer.process_payload(payload)

    assert msg.tenant_id == "inasc_tenant_test"


@pytest.mark.asyncio
async def test_process_payload_mensaje_no_texto_lanza_error():
    """Un mensaje de tipo 'image', 'audio' etc. debe levantar ValueError."""
    producer = WhatsAppProducer(tenant_id="inasc_001")
    payload = _make_payload(msg_type="image")

    with pytest.raises(ValueError, match="no soportado"):
        await producer.process_payload(payload)


@pytest.mark.asyncio
async def test_enqueue_llama_queue_manager():
    """enqueue() normaliza el payload y lo deposita en el QueueManager."""
    producer = WhatsAppProducer(tenant_id="inasc_001")
    payload = _make_payload(phone="573001111111", text="Cotización por favor.")

    with patch("src.core.producers.base.queue_manager") as mock_qm:
        mock_qm.enqueue_message = AsyncMock()
        await producer.enqueue(payload)
        mock_qm.enqueue_message.assert_awaited_once()
        enqueued_msg = mock_qm.enqueue_message.call_args[0][0]
        assert enqueued_msg.platform == "whatsapp"
        assert enqueued_msg.platform_user_id == "573001111111"
        assert enqueued_msg.content == "Cotización por favor."


@pytest.mark.asyncio
async def test_enqueue_mensaje_no_texto_no_encola():
    """Un mensaje de imagen no debe ser encolado — enqueue debe silenciarlo."""
    producer = WhatsAppProducer(tenant_id="inasc_001")
    payload = _make_payload(msg_type="audio")

    with patch("src.core.producers.base.queue_manager") as mock_qm:
        mock_qm.enqueue_message = AsyncMock()
        # enqueue llama process_payload internamente; si lanza ValueError,
        # el router lo captura y no lo encola. Verificamos que ValueError se propaga.
        with pytest.raises(ValueError):
            await producer.enqueue(payload)
        mock_qm.enqueue_message.assert_not_awaited()
