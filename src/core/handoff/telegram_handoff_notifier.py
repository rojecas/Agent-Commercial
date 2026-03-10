"""
telegram_handoff_notifier.py — Implementación Strategy para Telegram.

Notifica al asesor/grupo de Telegram cuando HandoffService detecta
un trigger de handoff. Reutiliza el httpx.AsyncClient del singleton
telegram_responder para evitar conexiones duplicadas.

Casos:
  notify_available()   → envía ficha del caso al TELEGRAM_ADVISOR_GROUP_ID + confirma al cliente
  notify_unavailable() → envía resumen al grupo para callback diferido + informa al cliente
"""
import logging
import os
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

from src.core.handoff.base_notifier import BaseHandoffNotifier

load_dotenv()
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADVISOR_GROUP_ID = os.getenv("TELEGRAM_ADVISOR_GROUP_ID", "")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


class TelegramHandoffNotifier(BaseHandoffNotifier):
    """
    Notifier de handoff para el canal Telegram.

    Usa sendMessage para transmitir la ficha del caso al grupo/asesor
    configurado en TELEGRAM_ADVISOR_GROUP_ID.

    Modo degradado: si TELEGRAM_BOT_TOKEN o TELEGRAM_ADVISOR_GROUP_ID
    no están configurados, loguea una advertencia y retorna el mensaje
    al cliente sin lanzar excepción.
    """

    def _is_configured(self) -> bool:
        return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_ADVISOR_GROUP_ID)

    async def _send_to_group(self, text: str) -> None:
        """Envía un mensaje al TELEGRAM_ADVISOR_GROUP_ID."""
        if not self._is_configured():
            logger.warning(
                "[TelegramHandoffNotifier] TELEGRAM_BOT_TOKEN o "
                "TELEGRAM_ADVISOR_GROUP_ID no configurados. Notificación omitida."
            )
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{TELEGRAM_API_BASE}/sendMessage",
                    json={
                        "chat_id": TELEGRAM_ADVISOR_GROUP_ID,
                        "text": text,
                        "parse_mode": "HTML",
                    },
                )
                if response.status_code != 200:
                    logger.error(
                        f"[TelegramHandoffNotifier] Error {response.status_code} "
                        f"al notificar al grupo: {response.text[:200]}"
                    )
                else:
                    logger.info(
                        f"[TelegramHandoffNotifier] Notificación enviada al grupo "
                        f"'{TELEGRAM_ADVISOR_GROUP_ID}'."
                    )
        except httpx.RequestError as e:
            logger.error(f"[TelegramHandoffNotifier] Error de red: {e}")

    async def notify_available(self, conversation, message, advisor, summary: str) -> str:
        """
        Notifica al grupo de Telegram que hay un caso listo para atención.

        La ficha incluye:
        - Asesor asignado
        - Canal de origen y user_id del cliente
        - Resumen del caso
        - Timestamp
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        ficha = (
            f"🔔 <b>Nuevo Handoff — Asesor Asignado: {advisor.name}</b>\n"
            f"─────────────────────────\n"
            f"📱 <b>Canal:</b> {message.platform}\n"
            f"👤 <b>Cliente ID:</b> <code>{message.platform_user_id}</code>\n"
            f"🆔 <b>Conv ID:</b> <code>{conversation.id}</code>\n"
            f"🕐 <b>Hora:</b> {timestamp}\n\n"
            f"📋 <b>Caso:</b>\n{summary}"
        )

        await self._send_to_group(ficha)

        return (
            f"✅ Te estamos conectando con <b>{advisor.name}</b>, "
            f"quien revisará tu caso y te contactará a la brevedad. "
            f"¡Gracias por tu paciencia! 🤝"
        )

    async def notify_unavailable(self, conversation, message, summary: str) -> str:
        """
        Notifica al grupo que hay un caso pendiente sin asesor disponible.
        El equipo debe hacer callback al cliente.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        ficha = (
            f"⏳ <b>Caso Pendiente — Sin Asesor Disponible</b>\n"
            f"─────────────────────────\n"
            f"📱 <b>Canal:</b> {message.platform}\n"
            f"👤 <b>Cliente ID:</b> <code>{message.platform_user_id}</code>\n"
            f"🆔 <b>Conv ID:</b> <code>{conversation.id}</code>\n"
            f"🕐 <b>Hora:</b> {timestamp}\n\n"
            f"📋 <b>Caso (requiere callback):</b>\n{summary}"
        )

        await self._send_to_group(ficha)

        return (
            "En este momento no tenemos asesores disponibles 😔\n\n"
            "He registrado tu caso completo y un asesor de nuestro equipo "
            "se pondrá en contacto contigo muy pronto. "
            "¡Gracias por tu comprensión! 📋"
        )
