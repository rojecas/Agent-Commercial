"""
whatsapp_handoff_notifier.py — Implementación Strategy para WhatsApp.

Notifica al asesor asignado vía WhatsApp cuando HandoffService detecta
un trigger de handoff. Reutiliza el singleton whatsapp_responder.
"""
import logging
import os
from datetime import datetime, timezone

from src.core.handoff.base_notifier import BaseHandoffNotifier
from src.core.whatsapp_responder import whatsapp_responder

logger = logging.getLogger(__name__)

WHATSAPP_SUPPORT_NUMBER = os.getenv("WHATSAPP_SUPPORT_NUMBER", "")


class WhatsAppHandoffNotifier(BaseHandoffNotifier):
    """
    Notifier de handoff para el canal WhatsApp (Meta Cloud API).

    Envía una ficha del caso detallada al whatsapp_number del asesor.
    Si no hay asesor disponible, envía la ficha a WHATSAPP_SUPPORT_NUMBER.
    """

    async def _send_notification(self, destination_number: str, text: str) -> None:
        """Helper para enviar vía whatsapp_responder con logging."""
        if not destination_number:
            logger.warning(
                "[WhatsAppHandoffNotifier] Destinatario no configurado. Notificación omitida."
            )
            return

        success = await whatsapp_responder.send_message(destination_number, text)
        if not success:
            logger.error(
                f"[WhatsAppHandoffNotifier] Falló el envío a +{destination_number}."
            )

    async def notify_available(self, conversation, message, advisor, summary: str) -> str:
        """
        Notifica al asesor asignado que hay un caso listo para atención en WhatsApp.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        ficha = (
            f"🟢 *Nuevo Handoff WhatsApp*\n"
            f"Asesor: {advisor.name}\n"
            f"---------------------------\n"
            f"👤 *Cliente:* {message.user_name or 'N/A'}\n"
            f"🆔 *ID:* {message.platform_user_id}\n"
            f"🕐 *Hora:* {timestamp}\n\n"
            f"📋 *Caso:*\n{summary}"
        )

        # 1. Notificar al asesor asignado
        if advisor.whatsapp_number:
            await self._send_notification(advisor.whatsapp_number, ficha)
        else:
            logger.warning(
                f"[WhatsAppHandoffNotifier] Asesor {advisor.name} no tiene whatsapp_number."
            )

        # 2. Retornar mensaje para el cliente
        return (
            f"✅ Te estamos conectando con *{advisor.name}*, "
            f"quien revisará tu caso y te contactará por este medio. "
            f"¡Gracias por tu paciencia! 🤝"
        )

    async def notify_unavailable(self, conversation, message, summary: str) -> str:
        """
        Notifica al número de soporte que hay un caso pendiente sin asesor.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        ficha = (
            f"⏳ *Caso WhatsApp PENDIENTE*\n"
            f"Sin asesor disponible.\n"
            f"---------------------------\n"
            f"👤 *Cliente:* {message.user_name or 'N/A'}\n"
            f"🆔 *ID:* {message.platform_user_id}\n"
            f"🕐 *Hora:* {timestamp}\n\n"
            f"📋 *Resumen para callback:*\n{summary}"
        )

        # 1. Notificar al soporte central
        if WHATSAPP_SUPPORT_NUMBER:
            await self._send_notification(WHATSAPP_SUPPORT_NUMBER, ficha)
        else:
            logger.warning(
                "[WhatsAppHandoffNotifier] WHATSAPP_SUPPORT_NUMBER no configurada."
            )

        # 2. Retornar mensaje para el cliente
        return (
            "En este momento no tenemos asesores disponibles 😔\n\n"
            "He registrado tu requerimiento y un asesor de nuestro equipo "
            "se pondrá en contacto contigo muy pronto por este medio. "
            "¡Gracias por tu comprensión! 📋"
        )
