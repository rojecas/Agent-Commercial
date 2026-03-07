import logging
import os
from typing import Any

from dotenv import load_dotenv

from src.core.producers.base import BaseProducer
from src.models.message import IncomingMessage

load_dotenv()
logger = logging.getLogger(__name__)

# tenant_id representa la EMPRESA (INASC S.A.S.), no el canal.
# El canal queda en IncomingMessage.platform ('whatsapp').
# Mismo patrón que TelegramProducer e WebSocketProducer.
TENANT_ID = os.getenv("TENANT_ID", "inasc_001")


class WhatsAppProducer(BaseProducer):
    """
    Producer para el canal WhatsApp (Meta Cloud API).

    Recibe el payload JSON completo del webhook de Meta y lo normaliza
    hacia el formato estándar IncomingMessage para que el Agent Loop
    lo procese exactamente igual que Telegram o el Widget Web.

    Estructura esperada del payload de Meta:
    {
      "object": "whatsapp_business_account",
      "entry": [{
        "changes": [{
          "value": {
            "messages": [{
              "from": "573001234567",
              "type": "text",
              "text": {"body": "Hola, ¿qué productos tienen?"}
            }],
            "contacts": [{"profile": {"name": "Juan Pérez"}}]
          }
        }]
      }]
    }

    Decisiones de diseño:
    - platform_user_id = número de teléfono (E.164, sin '+'), que es el
      identificador único del remitente y el destinatario de la respuesta.
    - Solo se procesan mensajes de tipo 'text'. Fotos, audio, documentos
      levantan ValueError para que el endpoint los ignore limpiamente.
    - El tenant_id viene del entorno del servidor, nunca del payload de Meta.
    """

    def __init__(self, tenant_id: str = TENANT_ID):
        self.tenant_id = tenant_id

    async def process_payload(self, raw_payload: Any) -> IncomingMessage:
        """
        Mapea un update de Meta WhatsApp al modelo IncomingMessage.
        Lanza ValueError si el mensaje no es de tipo texto.
        """
        try:
            entry = raw_payload["entry"][0]
            change = entry["changes"][0]["value"]
            message = change["messages"][0]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Payload de Meta malformado o sin mensajes: {e}")

        msg_type = message.get("type")
        if msg_type != "text":
            raise ValueError(
                f"Tipo de mensaje '{msg_type}' no soportado — ignorar "
                "(audio, imagen, documento, etc.)"
            )

        phone_number = message["from"]  # E.164 sin '+', ej: "573001234567"
        text_body = message["text"]["body"]

        # Nombre del contacto (opcional — no siempre lo envía Meta)
        contacts = change.get("contacts", [])
        user_name = None
        if contacts:
            user_name = contacts[0].get("profile", {}).get("name")

        logger.info(
            f"[WhatsAppProducer] Mensaje de +{phone_number}: '{text_body[:60]}'"
        )

        return IncomingMessage(
            platform="whatsapp",
            platform_user_id=phone_number,
            tenant_id=self.tenant_id,
            content=text_body,
            user_name=user_name,
        )
