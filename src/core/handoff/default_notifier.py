"""
default_notifier.py — Implementación fallback del BaseHandoffNotifier.

Se usa cuando el canal aún no tiene su propio XHandoffNotifier implementado
(ej. durante el desarrollo de #24 y #25). Solo loguea y retorna mensajes
genéricos — NO envía notificaciones reales al asesor.
"""
import logging
from src.core.handoff.base_notifier import BaseHandoffNotifier

logger = logging.getLogger(__name__)


class DefaultHandoffNotifier(BaseHandoffNotifier):
    """
    Notifier de fallback (solo log). Producción requiere el notifier
    específico del canal (TelegramHandoffNotifier, etc.).
    """

    async def notify_available(self, conversation, message, advisor, summary: str) -> str:
        logger.warning(
            f"[DefaultHandoffNotifier] Handoff a asesor '{advisor.name}' para "
            f"conversación {conversation.id} — canal '{message.platform}' sin notifier "
            f"específico. El asesor NO fue notificado por canal."
        )
        return (
            f"Te estamos conectando con {advisor.name}, quien te contactará en breve. "
            f"¡Gracias por tu paciencia! 🤝"
        )

    async def notify_unavailable(self, conversation, message, summary: str) -> str:
        logger.warning(
            f"[DefaultHandoffNotifier] Sin asesores disponibles para "
            f"conversación {conversation.id} — canal '{message.platform}'. "
            f"El equipo NO fue notificado. Resumen del caso: {summary[:100]}..."
        )
        return (
            "En este momento no tenemos asesores disponibles. "
            "He tomado nota de tu caso y un asesor se pondrá en contacto contigo "
            "a la brevedad. ¡Disculpa el inconveniente! 📋"
        )
