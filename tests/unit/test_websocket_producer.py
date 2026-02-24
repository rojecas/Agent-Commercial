"""
Tests unitarios para WebSocketProducer.

Verifica que process_payload() normaliza correctamente el JSON del Widget JS
al formato estándar IncomingMessage, sin necesidad de API real ni servidor.
"""
import pytest
from src.core.producers.websocket_producer import WebSocketProducer


@pytest.fixture
def producer():
    return WebSocketProducer(tenant_id="inasc_web")


@pytest.mark.asyncio
async def test_process_payload_fields_completos(producer):
    """
    Caso feliz: payload completo con user_name incluido.
    """
    raw = {
        "client_id": "user_abc_123",
        "text": "¿Tienen balanzas analíticas con resolución de 0.1 mg?",
        "user_name": "Carlos Martínez",
    }

    msg = await producer.process_payload(raw)

    assert msg.platform == "web"
    assert msg.platform_user_id == "user_abc_123"
    assert msg.tenant_id == "inasc_web"
    assert msg.content == "¿Tienen balanzas analíticas con resolución de 0.1 mg?"
    assert msg.user_name == "Carlos Martínez"


@pytest.mark.asyncio
async def test_process_payload_sin_user_name(producer):
    """
    user_name es opcional — el widget puede no enviarlo.
    """
    raw = {
        "client_id": "anonimo_456",
        "text": "Hola, necesito información sobre equipos HVAC.",
    }

    msg = await producer.process_payload(raw)

    assert msg.platform_user_id == "anonimo_456"
    assert msg.user_name is None
    assert msg.content == "Hola, necesito información sobre equipos HVAC."


@pytest.mark.asyncio
async def test_process_payload_tenant_id_inyectado_por_productor(producer):
    """
    El tenant_id debe venir del productor, nunca del payload del cliente.
    Esto garantiza aislamiento multi-tenant: un prospecto del Widget de INASC
    no puede inyectar un tenant_id diferente desde el navegador.
    """
    raw = {
        "client_id": "hacker_789",
        "text": "Mensaje",
        # El cliente NO envía tenant_id — lo asigna el servidor
    }

    msg = await producer.process_payload(raw)

    assert msg.tenant_id == "inasc_web"


@pytest.mark.asyncio
async def test_enqueue_llama_queue_manager(producer):
    """
    Verifica que enqueue() (heredado de BaseProducer) efectivamente
    llama a queue_manager.enqueue_message() con el mensaje normalizado.
    """
    from unittest.mock import AsyncMock, patch

    raw = {
        "client_id": "test_client",
        "text": "Mensaje de prueba de enqueue.",
    }

    with patch("src.core.queue_manager.queue_manager.enqueue_message", new_callable=AsyncMock) as mock_enqueue:
        await producer.enqueue(raw)
        mock_enqueue.assert_called_once()
        call_args = mock_enqueue.call_args[0][0]  # Primer argumento posicional
        assert call_args.platform == "web"
        assert call_args.platform_user_id == "test_client"
