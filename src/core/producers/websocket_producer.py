from typing import Any
from src.models.message import IncomingMessage
from src.core.producers.base import BaseProducer


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

    async def process_payload(self, raw_payload: Any) -> IncomingMessage:
        return IncomingMessage(
            platform="web",
            platform_user_id=raw_payload["client_id"],
            tenant_id=self.tenant_id,
            content=raw_payload["text"],
            user_name=raw_payload.get("user_name"),
        )
