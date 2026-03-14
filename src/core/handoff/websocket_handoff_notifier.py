"""
websocket_handoff_notifier.py — Implementación de handoff para el canal Web (WebSocket).
"""
import logging
from typing import TYPE_CHECKING
from src.core.handoff.base_notifier import BaseHandoffNotifier

if TYPE_CHECKING:
    from src.database.models import Advisor, Conversation
    from src.models.message import IncomingMessage

logger = logging.getLogger(__name__)

class WebSocketHandoffNotifier(BaseHandoffNotifier):
    """
    Notifier para el canal Web (Widget vía WebSocket).
    
    A diferencia de Telegram, no hay un grupo de asesores externo;
    el mensaje de handoff confirma al usuario en el chat web que el
    proceso de transferencia se ha iniciado.
    """

    async def notify_available(
        self,
        conversation: "Conversation",
        message: "IncomingMessage",
        advisor: "Advisor",
        summary: str,
    ) -> str:
        """
        Retorna el mensaje de conexión exitosa con un asesor.
        """
        logger.info(
            f"[WebSocketHandoff] Notificando disponibilidad de {advisor.name} "
            f"para la conversación web {conversation.id}."
        )
        
        # En el futuro, aquí se podría emitir un evento por WebSocket 
        # a un Dashboard de Asesores si existiera.
        
        return (
            f"¡Excelente noticia! Te acabo de conectar con **{advisor.name}**, "
            "quien se ha unido al chat y te responderá en breve. 🤝"
        )

    async def notify_unavailable(
        self,
        conversation: "Conversation",
        message: "IncomingMessage",
        summary: str,
    ) -> str:
        """
        Retorna el mensaje informativo cuando no hay asesores en línea.
        """
        logger.info(
            f"[WebSocketHandoff] Sin asesores para la conversación web {conversation.id}. "
            f"Flujo diferido (pending_callback) iniciado."
        )
        
        return (
            "En este momento no tenemos asesores disponibles en el chat. 📋\n\n"
            "He tomado nota de tu caso y un asesor se pondrá en contacto contigo "
            "a la brevedad por este medio o tus datos registrados. ¡Disculpa el inconveniente!"
        )
