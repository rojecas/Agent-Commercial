"""
Tests funcionales para el endpoint WebSocket /ws/chat/{client_id}.

DISEÑO DE LOS TESTS:
El TestClient síncrono de Starlette no puede ejecutar el Agent Loop de background
(asyncio.create_task en un hilo de anyio) de forma confiable bajo pytest. Intentar
testear el pipeline completo (WS → queue → LLM → send_to_client) con TestClient
produce un deadlock: el hilo del test bloquea en ws.receive_json() mientras el
event loop espera poder dar turno al agent loop.

Por eso, los tests funcionales aquí mockan WebSocketProducer.enqueue para que
inyecte la respuesta DIRECTAMENTE en connection_manager, sin pasar por el agent loop.

Esto prueba lo que importa para este Issue:
  1. El endpoint acepta conexiones WS y lee mensajes JSON.
  2. El client_id de la URL se inyecta correctamente al payload.
  3. El endpoint espera en response_queue y reenvía la respuesta al socket.
  4. El formato de respuesta es {"role": "agent", "content": "..."}.

El pipeline completo (WS → queue → LLM → DB → response) está cubierto por:
  - tests/unit/test_websocket_producer.py (normalización y enqueue).
  - Tests de integración de la BD (Issue #3).
  - Verificación manual con el servidor real corriendo.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.core.connection_manager import connection_manager
from src.core.producers.websocket_producer import WebSocketProducer


@pytest.fixture
def client():
    return TestClient(app)


def _make_instant_enqueue(response_text: str):
    """
    Fábrica de mocks de enqueue que inyecta una respuesta instantánea
    en la cola privada del cliente, simulando lo que haría el agent loop.
    """
    async def mock_enqueue(self, raw_payload):
        client_id = raw_payload.get("client_id")
        await connection_manager.send_to_client(client_id, response_text)
    return mock_enqueue


def test_websocket_connect_and_single_response(client):
    """
    Caso base: un cliente conecta, envía un mensaje y recibe respuesta.
    Verifica el flujo de entrada/salida y el formato de respuesta.
    """
    expected = "Ofrecemos balanzas OHAUS con resolución de 0.1 mg. 📡"

    with patch.object(WebSocketProducer, "enqueue", _make_instant_enqueue(expected)):
        with client.websocket_connect("/ws/chat/test_prospecto_01") as ws:
            ws.send_json({
                "text": "¿Qué balanzas analíticas tienen?",
                "user_name": "Carlos"
            })
            response = ws.receive_json()

    assert response["role"] == "agent"
    assert response["content"] == expected


def test_websocket_client_id_injected_from_url(client):
    """
    El client_id viene de la URL, no del payload del cliente.
    Verifica que el endpoint lo inyecta antes de llamar a enqueue.
    """
    received_payloads = []

    async def capture_enqueue(self, raw_payload):
        received_payloads.append(dict(raw_payload))
        await connection_manager.send_to_client(
            raw_payload["client_id"], "respuesta"
        )

    with patch.object(WebSocketProducer, "enqueue", capture_enqueue):
        with client.websocket_connect("/ws/chat/cliente_xyz_99") as ws:
            ws.send_json({"text": "Hola"})
            ws.receive_json()

    assert len(received_payloads) == 1
    assert received_payloads[0]["client_id"] == "cliente_xyz_99"


def test_websocket_multiple_turns(client):
    """
    Múltiples mensajes en el mismo socket — el loop while True del endpoint
    debe procesar cada turno de forma independiente.
    """
    turns = ["Respuesta A", "Respuesta B"]
    turn_idx = [0]

    async def sequential_enqueue(self, raw_payload):
        resp = turns[turn_idx[0]]
        turn_idx[0] += 1
        await connection_manager.send_to_client(raw_payload["client_id"], resp)

    with patch.object(WebSocketProducer, "enqueue", sequential_enqueue):
        with client.websocket_connect("/ws/chat/multiturn_user") as ws:
            for expected in turns:
                ws.send_json({"text": "Mensaje de prueba"})
                response = ws.receive_json()
                assert response["content"] == expected


def test_simulate_endpoint_no_regression(client):
    """
    No-regresión: /simulate/message debe seguir respondiendo 200 OK
    sin verse afectado por los cambios de este Issue.
    """
    with patch("src.core.queue_manager.queue_manager.enqueue_message",
               new_callable=AsyncMock):
        response = client.post("/simulate/message", json={
            "platform": "simulator",
            "platform_user_id": "sim_user_01",
            "tenant_id": "test_tenant",
            "content": "Prueba de regresión",
        })

    assert response.status_code == 200
    assert response.json()["status"] == "success"
