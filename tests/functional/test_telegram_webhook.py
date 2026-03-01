"""
Tests funcionales para el endpoint POST /webhook/telegram.
Verifican el protocolo HTTP del webhook sin llamar al LLM ni a Telegram.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

VALID_UPDATE = {
    "update_id": 888001,
    "message": {
        "chat": {"id": 111222},
        "from": {"username": "prospecto_real"},
        "text": "Buenos días, necesito información sobre espectrofotómetros.",
    }
}

VALID_HEADERS = {"content-type": "application/json"}


class TestTelegramWebhookEndpoint:

    def test_webhook_retorna_200_inmediato(self):
        """El endpoint responde 200 OK inmediatamente, sin esperar al LLM."""
        with patch("src.api.routers.telegram.TelegramProducer") as MockProducer:
            mock_instance = MockProducer.return_value
            mock_instance.enqueue = AsyncMock()

            response = client.post(
                "/webhook/telegram",
                json=VALID_UPDATE,
                headers=VALID_HEADERS,
            )

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_webhook_encola_mensaje(self):
        """El endpoint encola el mensaje via TelegramProducer.enqueue()."""
        with patch("src.api.routers.telegram.TelegramProducer") as MockProducer:
            mock_instance = MockProducer.return_value
            mock_instance.enqueue = AsyncMock()

            client.post(
                "/webhook/telegram",
                json=VALID_UPDATE,
                headers=VALID_HEADERS,
            )

            mock_instance.enqueue.assert_called_once_with(VALID_UPDATE)

    def test_webhook_ignora_update_sin_mensaje_texto(self):
        """Updates de fotos, stickers, etc. responden 200 sin encolar nada."""
        update_foto = {
            "update_id": 888002,
            "message": {
                "chat": {"id": 111222},
                "from": {"username": "test"},
                "photo": [{"file_id": "photo_abc"}],
            }
        }

        with patch("src.api.routers.telegram.TelegramProducer") as MockProducer:
            mock_instance = MockProducer.return_value
            mock_instance.enqueue = AsyncMock()

            response = client.post(
                "/webhook/telegram",
                json=update_foto,
                headers=VALID_HEADERS,
            )

            assert response.status_code == 200
            assert response.json() == {"ok": True}
            mock_instance.enqueue.assert_not_called()

    def test_webhook_rechaza_secret_token_invalido(self):
        """Si TELEGRAM_WEBHOOK_SECRET está definido, un token inválido recibe 403."""
        with patch.dict("os.environ", {"TELEGRAM_WEBHOOK_SECRET": "mi_secret_correcto"}):
            # Recargamos el módulo para que lea la variable de entorno actualizada
            import importlib
            import src.api.routers.telegram as tg_module
            importlib.reload(tg_module)

            response = client.post(
                "/webhook/telegram",
                json=VALID_UPDATE,
                headers={
                    "content-type": "application/json",
                    "X-Telegram-Bot-Api-Secret-Token": "token_incorrecto",
                },
            )

        assert response.status_code == 403
