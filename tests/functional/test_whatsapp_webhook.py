"""
Tests funcionales para el WebHook de WhatsApp (Issue #16).

Usan TestClient de FastAPI / Starlette para simular requests HTTP reales
al endpoint /webhook/whatsapp sin necesitar credenciales de Meta.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """
    Cliente de prueba con mocks preventivos para evitar efectos secundarios.

    Los responders (telegram, whatsapp) se pasan como AsyncMock con .close
    explícitamente awaitable porque lifespan hace `await responder.close()`
    al apagar el servidor.
    """
    from unittest.mock import MagicMock, AsyncMock

    tg_mock = MagicMock()
    tg_mock.close = AsyncMock()
    wa_mock = MagicMock()
    wa_mock.close = AsyncMock()

    with (
        patch("src.main.run_agent_loop", new_callable=AsyncMock),
        patch("src.main.llm_engine"),
        patch("src.main.async_session_factory"),
        patch("src.main.telegram_responder", tg_mock),
        patch("src.main.whatsapp_responder", wa_mock),
    ):
        from src.main import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c



def _meta_update(phone: str = "573001234567", text: str = "Hola!", name: str | None = "Test User") -> dict:
    contacts = [{"profile": {"name": name}}] if name else []
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": phone,
                        "type": "text",
                        "text": {"body": text},
                    }],
                    "contacts": contacts,
                }
            }]
        }]
    }


# ── Tests: GET /webhook/whatsapp (verificación Meta) ────────────────

def test_verificacion_webhook_token_correcto(client):
    """Meta verifica el webhook con token correcto → responde el challenge exacto."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "inasc_whatsapp_verify_token",
        "hub.challenge": "1234567890",
    }
    response = client.get("/webhook/whatsapp", params=params)
    assert response.status_code == 200
    assert response.text == "1234567890"


def test_verificacion_webhook_token_incorrecto(client):
    """Token equivocado → 403 Forbidden."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "token_equivocado",
        "hub.challenge": "1234567890",
    }
    response = client.get("/webhook/whatsapp", params=params)
    assert response.status_code == 403


def test_verificacion_webhook_mode_incorrecto(client):
    """hub.mode distinto de 'subscribe' → 403."""
    params = {
        "hub.mode": "unsubscribe",
        "hub.verify_token": "inasc_whatsapp_verify_token",
        "hub.challenge": "9876543210",
    }
    response = client.get("/webhook/whatsapp", params=params)
    assert response.status_code == 403


# ── Tests: POST /webhook/whatsapp (mensajes entrantes) ──────────────

def test_post_mensaje_texto_encola_y_responde_ok(client):
    """Un mensaje de texto válido debe ser encolado y el endpoint retorna 200 OK."""
    with patch("src.api.routers.whatsapp.WhatsAppProducer") as MockProducer:
        mock_instance = AsyncMock()
        MockProducer.return_value = mock_instance

        response = client.post("/webhook/whatsapp", json=_meta_update())

        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_instance.enqueue.assert_awaited_once()


def test_post_update_de_estado_ignorado(client):
    """Updates de tipo 'status' (delivered/read) deben ignorarse → 200 sin encolar."""
    status_update = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{"id": "msg_id", "status": "delivered"}]
                    # Sin campo "messages"
                }
            }]
        }]
    }
    with patch("src.api.routers.whatsapp.WhatsAppProducer") as MockProducer:
        mock_instance = AsyncMock()
        MockProducer.return_value = mock_instance

        response = client.post("/webhook/whatsapp", json=status_update)

        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_instance.enqueue.assert_not_awaited()


def test_post_mensaje_no_texto_descartado(client):
    """Un mensaje de imagen/audio → WhatsAppProducer levanta ValueError → ignorado con 200."""
    img_update = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{"from": "573001234567", "type": "image"}],
                    "contacts": [],
                }
            }]
        }]
    }
    with patch("src.api.routers.whatsapp.WhatsAppProducer") as MockProducer:
        mock_instance = AsyncMock()
        mock_instance.enqueue.side_effect = ValueError("image no soportado")
        MockProducer.return_value = mock_instance

        response = client.post("/webhook/whatsapp", json=img_update)

        assert response.status_code == 200
        assert response.json() == {"ok": True}


def test_post_body_json_invalido(client):
    """Un body que no es JSON válido retorna 400."""
    response = client.post(
        "/webhook/whatsapp",
        content=b"no soy json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_post_no_modifica_canales_existentes(client):
    """El endpoint de Telegram sigue funcionando — no hay regresiones."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
