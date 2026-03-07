import logging
import os
from typing import Any

from dotenv import load_dotenv

from src.core.producers.base import BaseProducer
from src.models.message import IncomingMessage

load_dotenv()
logger = logging.getLogger(__name__)

# tenant_id representa la EMPRESA (INASC S.A.S.), no el canal.
# El canal queda en IncomingMessage.platform ('telegram', 'web', etc.)
# Fix Issue #18: unificar tenant_id en todos los Producers.
TENANT_ID = os.getenv("TENANT_ID", "inasc_001")


class TelegramProducer(BaseProducer):
    """
    Producer para el canal Telegram Webhook.

    Recibe el payload JSON completo del update de Telegram y lo normaliza
    hacia el formato estándar IncomingMessage para que el Agent Loop lo procese.

    Diseño:
    - El tenant_id se lee de TENANT_ID en .env (representa la empresa, no el canal).
    - El canal queda en platform='telegram' del IncomingMessage.
    - El platform_user_id es el chat_id de Telegram (str) para que
      TelegramResponder pueda construir la respuesta de vuelta.
    - Mensajes sin campo 'text' (fotos, stickers, etc.) levantan ValueError
      para que el endpoint los ignore limpiamente.
    """

    def __init__(self, tenant_id: str = TENANT_ID):
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
