import logging
import os
from typing import Optional

import httpx
from dotenv import load_dotenv

from src.core.telegram_utils import chunk_telegram_message, escape_html_for_telegram

load_dotenv()
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


class TelegramResponder:
    """
    Singleton responsable de enviar respuestas del agente al canal Telegram.

    Es el equivalente simétrico de ConnectionManager.send_to_client() para WebSocket,
    pero en lugar de poner en una cola asyncio, hace un HTTP POST a la API de Telegram.

    Diseño:
    - Usa httpx.AsyncClient con keep-alive para reutilizar conexiones TCP.
    - Aplica chunking automático para respuestas > 4096 caracteres.
    - Escapa HTML antes de enviar (parse_mode='HTML').
    - Los errores de red se loguean sin re-lanzar para no romper el event loop.
    """

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy initialization del cliente HTTP (evita crear el client en import time)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def send_message(self, chat_id: str, text: str) -> None:
        """
        Envía la respuesta del agente al chat_id de Telegram indicado.

        Si la respuesta supera 4096 caracteres, se divide en múltiples mensajes.
        Cada chunk se envía por separado manteniendo el orden.

        Args:
            chat_id: ID del chat de Telegram (como string, viene de platform_user_id).
            text:    Texto de la respuesta generada por el LLM.
        """
        if not TELEGRAM_BOT_TOKEN:
            logger.warning("[TelegramResponder] TELEGRAM_BOT_TOKEN no configurado. Respuesta no enviada.")
            return

        safe_text = escape_html_for_telegram(text)
        chunks = chunk_telegram_message(safe_text)

        for i, chunk in enumerate(chunks):
            try:
                response = await self.client.post(
                    f"{TELEGRAM_API_BASE}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": chunk,
                        "parse_mode": "HTML",
                    },
                )
                if response.status_code == 200:
                    logger.info(
                        f"[TelegramResponder] Chunk {i+1}/{len(chunks)} enviado a chat_id={chat_id}."
                    )
                else:
                    logger.error(
                        f"[TelegramResponder] Error {response.status_code} al enviar "
                        f"chunk {i+1} a chat_id={chat_id}: {response.text[:200]}"
                    )
            except httpx.RequestError as e:
                logger.error(
                    f"[TelegramResponder] Error de red al enviar a chat_id={chat_id}: {e}"
                )

    async def close(self) -> None:
        """Cierra el cliente HTTP. Llamar en el lifespan shutdown de FastAPI."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Instancia global Singleton
telegram_responder = TelegramResponder()
