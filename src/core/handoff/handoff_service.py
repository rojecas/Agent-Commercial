"""
handoff_service.py — Orquestador central del mecanismo de handoff.

Detecta los dos triggers de handoff, verifica disponibilidad de asesores
en BD y delega la notificación al XHandoffNotifier del canal correcto
(patrón Strategy). El HandoffService no conoce los detalles de ningún canal.
"""
import logging
from typing import Optional, TYPE_CHECKING

from src.database import crud
from src.database.models import Advisor
from src.core.handoff.base_notifier import BaseHandoffNotifier
from src.core.handoff.default_notifier import DefaultHandoffNotifier

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.database.models import Conversation
    from src.models.message import IncomingMessage

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────

# Señal que el LLM inyecta al final de su respuesta para indicar handoff autónomo
HANDOFF_SIGNAL = "[HANDOFF_REQUESTED]"

# Palabras/frases que activan el Trigger A (usuario pide asesor explícitamente)
HANDOFF_KEYWORDS = [
    "hablar con una persona",
    "hablar con alguien",
    "hablar con un asesor",
    "quiero un asesor",
    "necesito un asesor",
    "asesor humano",
    "persona real",
    "agente humano",
    "representante",
    "vendedor",
    "me atiendan",
    "atención humana",
]


class HandoffService:
    """
    Servicio singleton que orquesta la transferencia de conversaciones.

    Flujo:
    1. detect_trigger()     → ¿hay un trigger A o B activo?
    2. execute()            → verifica advisor en BD, cambia status, delega notificación
    3. _get_notifier()      → selecciona el XHandoffNotifier según el canal
    4. _generate_summary()  → resumen del contexto para el asesor (placeholder en v1)

    Uso en main.py:
        handoff_msg = await handoff_service.execute(session, conversation, message)
        if handoff_msg:
            response_text = handoff_msg  # reemplaza la respuesta normal del LLM
    """

    def detect_trigger(self, user_msg: str, bot_response: str) -> bool:
        """
        Retorna True si alguno de los dos triggers de handoff está activo.

        Trigger A (explícito): el usuario pide hablar con una persona.
        Trigger B (autónomo):  el LLM incluyó [HANDOFF_REQUESTED] en su respuesta.
        """
        user_lower = user_msg.lower()
        trigger_a = any(kw in user_lower for kw in HANDOFF_KEYWORDS)
        trigger_b = HANDOFF_SIGNAL in bot_response

        if trigger_a:
            logger.info("[HandoffService] Trigger A detectado — usuario pidió asesor.")
        if trigger_b:
            logger.info("[HandoffService] Trigger B detectado — LLM solicitó handoff.")

        return trigger_a or trigger_b

    def strip_signal(self, response: str) -> str:
        """
        Elimina [HANDOFF_REQUESTED] del texto antes de enviarlo al canal.
        El cliente nunca debe ver la señal interna.
        """
        return response.replace(HANDOFF_SIGNAL, "").strip()

    def _get_notifier(self, platform: str) -> BaseHandoffNotifier:
        """
        Factory method — selecciona el notifier según el canal.

        Registro de notifiers. Al implementar #24 (Telegram) y #25 (WebSocket),
        se registran aquí sin tocar ningún otro código.
        """
        from src.core.handoff.telegram_handoff_notifier import TelegramHandoffNotifier
        from src.core.handoff.websocket_handoff_notifier import WebSocketHandoffNotifier
        from src.core.handoff.whatsapp_handoff_notifier import WhatsAppHandoffNotifier

        registry: dict[str, BaseHandoffNotifier] = {
            "telegram": TelegramHandoffNotifier(),
            "web": WebSocketHandoffNotifier(),
            "whatsapp": WhatsAppHandoffNotifier(),
        }

        notifier = registry.get(platform)
        if notifier is None:
            logger.debug(
                f"[HandoffService] No hay notifier específico para '{platform}'. "
                f"Usando DefaultHandoffNotifier."
            )
            notifier = DefaultHandoffNotifier()

        return notifier

    def _generate_summary(self, context_messages: list) -> str:
        """
        Genera un resumen del caso a partir del historial de conversación.

        v1: concatena los últimos mensajes del usuario como texto plano.
        v2 (TODO): llamar al LLM para generar un resumen estructurado.
        """
        user_messages = [
            msg["content"] for msg in context_messages
            if msg.get("role") == "user"
        ]
        if not user_messages:
            return "Sin contexto disponible."
        # Toma los últimos 3 mensajes del usuario como resumen
        snippet = " | ".join(user_messages[-3:])
        return f"Resumen del caso: {snippet[:500]}"

    async def execute(
        self,
        session: "AsyncSession",
        conversation: "Conversation",
        message: "IncomingMessage",
        context_messages: Optional[list] = None,
    ) -> Optional[str]:
        """
        Ejecuta el handoff completo si detect_trigger() retorna True.

        1. Verifica disponibilidad de asesores en BD.
        2. Cambia conversation.status en BD.
        3. Notifica vía XHandoffNotifier del canal.
        4. Retorna el mensaje a enviar al cliente, o None si no hubo handoff.

        IMPORTANTE: No hace commit — el caller (main.py) sigue siendo
        responsable del session.commit() al final de process_single_message().
        """
        summary = self._generate_summary(context_messages or [])
        notifier = self._get_notifier(message.platform)

        # Buscar asesor disponible — capturar errores de BD para no romper el flujo
        advisor: Optional[Advisor] = None
        try:
            advisor = await crud.get_available_advisor(session, message.tenant_id)
            if advisor:
                logger.info(
                    f"[HandoffService] ✅ Asesor encontrado: '{advisor.name}' "
                    f"(id={advisor.id}) para tenant='{message.tenant_id}'."
                )
            else:
                logger.info(
                    f"[HandoffService] ⚠️  Sin asesores disponibles "
                    f"para tenant='{message.tenant_id}'."
                )
        except Exception as db_err:
            logger.error(
                f"[HandoffService] ❌ Error consultando asesores en BD: {db_err}. "
                f"Cayendo a flujo pending_callback."
            )

        if advisor:
            await crud.set_conversation_status(
                session, conversation.id, message.tenant_id, "handed_off"
            )
            client_message = await notifier.notify_available(
                conversation, message, advisor, summary
            )
        else:
            await crud.set_conversation_status(
                session, conversation.id, message.tenant_id, "pending_callback"
            )
            client_message = await notifier.notify_unavailable(
                conversation, message, summary
            )

        return client_message


# Singleton global — importar en main.py
handoff_service = HandoffService()
