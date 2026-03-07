import os
from typing import Any
from dotenv import load_dotenv
from src.models.message import IncomingMessage
from src.core.producers.base import BaseProducer

load_dotenv()

# tenant_id representa la EMPRESA (INASC S.A.S.), no el canal.
# El canal ya queda en IncomingMessage.platform ('web', 'telegram', etc.)
# Fix Issue #18: unificar tenant_id en todos los Producers.
TENANT_ID = os.getenv("TENANT_ID", "inasc_001")


class WebSocketProducer(BaseProducer):
    """
    Producer para el canal Web (WebSocket).

    Hereda de BaseProducer, por lo que el flujo completo de:
      raw_payload → IncomingMessage → queue_manager.enqueue_message()
    ya está implementado en BaseProducer.enqueue().

    Solo debemos implementar process_payload() para mapear el JSON
    que manda el Widget JS del navegador al formato estándar IncomingMessage.

    Payload esperado del Widget JS:
    {
        "client_id": "usuario_123",   # Inyectado por el endpoint WS desde la URL
        "text":      "Hola, ¿tienen balanzas analíticas?",
        "user_name": "Juan Pérez"     # Opcional
    }
    """

    def __init__(self, tenant_id: str = TENANT_ID):
        self.tenant_id = tenant_id

    async def process_payload(self, raw_payload: Any) -> IncomingMessage:
        return IncomingMessage(
            platform="web",
            platform_user_id=raw_payload["client_id"],
            tenant_id=self.tenant_id,
            content=raw_payload["text"],
            user_name=raw_payload.get("user_name"),
        )
