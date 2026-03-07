import logging
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Credenciales de la Meta Cloud API — configurar en .env
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
META_API_VERSION = "v19.0"
META_API_URL = f"https://graph.facebook.com/{META_API_VERSION}"


class WhatsAppResponder:
    """
    Singleton que envía respuestas al usuario vía Meta WhatsApp Cloud API.

    Usa httpx.AsyncClient para no bloquear el Event Loop de FastAPI.
    El cliente HTTP se inicializa con un timeout razonable y se reutiliza
    durante toda la vida del servidor (patrón idéntico a TelegramResponder).

    Endpoint Meta:
        POST https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages
        Authorization: Bearer {WHATSAPP_API_TOKEN}
        Content-Type: application/json

    Body:
        {
          "messaging_product": "whatsapp",
          "to": "{phone_number}",
          "type": "text",
          "text": { "body": "{message_text}" }
        }
    """

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=15.0)

    async def send_message(self, phone_number: str, text: str) -> bool:
        """
        Envía un mensaje de texto al número de WhatsApp dado.

        Args:
            phone_number: Número E.164 sin '+' (ej: "573001234567")
            text:         Texto de la respuesta del agente

        Returns:
            True si Meta aceptó el mensaje (HTTP 200), False si hubo error.

        Nota: Si WHATSAPP_API_TOKEN o WHATSAPP_PHONE_NUMBER_ID no están
        configurados (modo desarrollo sin cuenta Meta), el método loguea un
        aviso y retorna False sin lanzar excepción.
        """
        if not WHATSAPP_API_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            logger.warning(
                "[WhatsAppResponder] WHATSAPP_API_TOKEN o WHATSAPP_PHONE_NUMBER_ID "
                "no configurados. Respuesta NO enviada a WhatsApp "
                f"(destino: +{phone_number}). "
                "Configura las variables en .env para modo producción."
            )
            return False

        url = f"{META_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": text},
        }

        try:
            response = await self._client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(
                f"[WhatsAppResponder] ✅ Mensaje enviado a +{phone_number}. "
                f"Meta message_id: {response.json().get('messages', [{}])[0].get('id', 'N/A')}"
            )
            return True
        except httpx.HTTPStatusError as e:
            logger.error(
                f"[WhatsAppResponder] ❌ Error HTTP {e.response.status_code} "
                f"enviando a +{phone_number}: {e.response.text}"
            )
            return False
        except httpx.RequestError as e:
            logger.error(
                f"[WhatsAppResponder] ❌ Error de red enviando a +{phone_number}: {e}"
            )
            return False

    async def close(self):
        """Cierra el cliente HTTP limpiamente al apagar el servidor."""
        await self._client.aclose()
        logger.info("[WhatsAppResponder] HTTP client closed.")


# Instancia global Singleton — importar en main.py
whatsapp_responder = WhatsAppResponder()
