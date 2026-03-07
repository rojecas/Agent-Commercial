"""
Tests unitarios para TelegramProducer.
Verifica que el payload del webhook de Telegram se normaliza correctamente
hacia el modelo IncomingMessage sin llamar a dependencias externas.
"""
import pytest
from unittest.mock import AsyncMock, patch

from src.core.producers.telegram_producer import TelegramProducer


VALID_UPDATE = {
    "update_id": 999001,
    "message": {
        "chat": {"id": 456789},
        "from": {"username": "test_user", "first_name": "Test"},
        "text": "Hola, ¿qué balanzas tienen disponibles?",
    }
}


class TestTelegramProducer:

    @pytest.mark.asyncio
    async def test_process_payload_mapea_campos_correctos(self):
        """El payload de Telegram se mapea correctamente hacia IncomingMessage."""
        producer = TelegramProducer(tenant_id="inasc_telegram")
        msg = await producer.process_payload(VALID_UPDATE)

        assert msg.platform == "telegram"
        assert msg.platform_user_id == "456789"
        assert msg.content == "Hola, ¿qué balanzas tienen disponibles?"
        assert msg.user_name == "test_user"

    @pytest.mark.asyncio
    async def test_process_payload_tenant_id_inyectado_por_servidor(self):
        """El tenant_id viene del entorno del servidor, nunca del payload de Telegram."""
        producer = TelegramProducer(tenant_id="inasc_telegram")
        # Añadimos un campo 'tenant_id' falso en el payload para verificar que se ignora
        malicious_update = dict(VALID_UPDATE)
        malicious_update["tenant_id"] = "tenant_hackeado"
        msg = await producer.process_payload(malicious_update)

        assert msg.tenant_id == "inasc_telegram"
        assert msg.tenant_id != "tenant_hackeado"

    @pytest.mark.asyncio
    async def test_process_payload_update_sin_text_lanza_value_error(self):
        """Un update sin 'text' (foto, sticker) debe levantar ValueError."""
        producer = TelegramProducer(tenant_id="inasc_telegram")
        update_sin_texto = {
            "update_id": 999002,
            "message": {
                "chat": {"id": 456789},
                "from": {"username": "test_user"},
                # Sin campo 'text': es una foto o sticker
                "photo": [{"file_id": "abc123"}],
            }
        }
        with pytest.raises(ValueError):
            await producer.process_payload(update_sin_texto)

    @pytest.mark.asyncio
    async def test_enqueue_llama_queue_manager(self):
        """enqueue() debe normalizar el payload y llamar a queue_manager.enqueue_message()."""
        producer = TelegramProducer(tenant_id="inasc_telegram")

        with patch(
            "src.core.producers.telegram_producer.TelegramProducer.process_payload",
            new_callable=AsyncMock
        ) as mock_process, patch(
            "src.core.producers.base.queue_manager"
        ) as mock_queue:
            from src.models.message import IncomingMessage
            mock_process.return_value = IncomingMessage(
                platform="telegram",
                platform_user_id="456789",
                tenant_id="inasc_telegram",
                content="Hola",
            )
            mock_queue.enqueue_message = AsyncMock()

            await producer.enqueue(VALID_UPDATE)

            mock_process.assert_called_once_with(VALID_UPDATE)
            mock_queue.enqueue_message.assert_called_once()
