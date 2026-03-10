"""
base_notifier.py — Interfaz Strategy para notificadores de handoff.

Cada canal implementa su propia subclase para manejar la notificación
al asesor y al cliente de forma específica (Telegram, WhatsApp, WebSocket).
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.database.models import Advisor, Conversation
    from src.models.message import IncomingMessage


class BaseHandoffNotifier(ABC):
    """
    Interfaz Strategy para el mecanismo de handoff.

    Cada canal (Telegram #24, WhatsApp #23 WA, WebSocket #25) implementa
    esta interfaz. El HandoffService selecciona el notifier correcto según
    el platform de IncomingMessage, delegando la lógica canal-específica.

    Contrato:
    - notify_available()   → retorna el mensaje a enviar AL CLIENTE
                             (el notifier también notifica al asesor internamente)
    - notify_unavailable() → retorna el mensaje a enviar AL CLIENTE
                             (el notifier también notifica al equipo internamente)
    """

    @abstractmethod
    async def notify_available(
        self,
        conversation: "Conversation",
        message: "IncomingMessage",
        advisor: "Advisor",
        summary: str,
    ) -> str:
        """
        Se llama cuando hay un asesor disponible.

        Debe:
        1. Notificar al asesor (por su canal de contacto) con el contexto del caso.
        2. Retornar el mensaje que el bot enviará al cliente confirmando la transferencia.

        Args:
            conversation: Objeto Conversation con id, status, tenant_id.
            message:      IncomingMessage del cliente (platform_user_id, content, etc.).
            advisor:      Asesor asignado (name, telegram_user_id, whatsapp_number, email).
            summary:      Resumen del caso generado por el LLM.
        """

    @abstractmethod
    async def notify_unavailable(
        self,
        conversation: "Conversation",
        message: "IncomingMessage",
        summary: str,
    ) -> str:
        """
        Se llama cuando NO hay asesores disponibles.

        Debe:
        1. Notificar al equipo por canal interno (grupo, email, etc.) con el resumen.
        2. Retornar el mensaje que el bot enviará al cliente informando del callback.

        Args:
            conversation: Objeto Conversation.
            message:      IncomingMessage del cliente.
            summary:      Resumen del caso generado por el LLM.
        """
