import logging
import os
from typing import Any

from dotenv import load_dotenv

from src.core.producers.base import BaseProducer
from src.models.message import IncomingMessage

load_dotenv()
logger = logging.getLogger(__name__)

# Tenant por defecto para el canal Telegram.
# Configurable en .env como TELEGRAM_CHANNEL_TENANT_ID.
TELEGRAM_TENANT_ID = os.getenv("TELEGRAM_CHANNEL_TENANT_ID", "inasc_telegram")


class TelegramProducer(BaseProducer):
    """
    Producer para el canal Telegram Webhook.

    Recibe el payload JSON completo del update de Telegram y lo normaliza
    hacia el formato estándar IncomingMessage para que el Agent Loop lo procese.

    Diseño:
    - El tenant_id se inyecta desde el entorno del servidor (nunca del payload).
    - El platform_user_id es el chat_id de Telegram (str) para garantizar
      que TelegramResponder pueda construir la respuesta de vuelta.
    - Mensajes sin campo 'text' (fotos, stickers, etc.) levantan ValueError
      para que el endpoint los ignore limpiamente.
    """

    def __init__(self, tenant_id: str = TELEGRAM_TENANT_ID):
        self.tenant_id = tenant_id

    async def process_payload(self, raw_payload: Any) -> IncomingMessage:
        """
        Mapea un update de Telegram al modelo IncomingMessage.

        Estructura esperada del update:
        {
          "update_id": 123456,
          "message": {
            "chat": {"id": 789},
            "from": {"username": "john_doe", "first_name": "John"},
            "text": "Hola, ¿qué productos tienen?"
          }
        }
        """
        message = raw_payload.get("message", {})
        text = message.get("text")

        if not text:
            raise ValueError("Update sin campo 'text' — ignorar (foto, sticker, etc.)")

        chat_id = str(message["chat"]["id"])
        from_data = message.get("from", {})
        user_name = from_data.get("username") or from_data.get("first_name")

        logger.info(f"[TelegramProducer] Mensaje de chat_id={chat_id}: '{text[:60]}'")

        return IncomingMessage(
            platform="telegram",
            platform_user_id=chat_id,
            tenant_id=self.tenant_id,
            content=text,
            user_name=user_name,
        )
