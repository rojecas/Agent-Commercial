import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Singleton que administra todas las conexiones WebSocket activas.

    DECISIÓN ARQUITECTÓNICA (ver implementation_plan.md — ADR):
    Mantiene dos diccionarios paralelos indexados por client_id:
      - active_connections: el objeto WebSocket para enviar mensajes.
      - response_queues:    una asyncio.Queue privada por cliente, usada como
                            puente entre el worker del Agent Loop (background)
                            y el endpoint WS (que espera la respuesta del LLM).

    De este modo, N clientes y M tenants concurrentes nunca mezclan sus
    respuestas: cada cliente solo puede leer de SU propia cola.
    """

    def __init__(self):
        # client_id → WebSocket activo
        self.active_connections: dict[str, WebSocket] = {}
        # client_id → Cola privada de respuesta del LLM
        self.response_queues: dict[str, asyncio.Queue] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """
        Acepta la conexión WS y registra al cliente con su cola privada.
        Llamar siempre ANTES de entrar al loop de recepción de mensajes.
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.response_queues[client_id] = asyncio.Queue()
        logger.info(f"[WS] Client '{client_id}' connected. "
                    f"Total active: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """
        Elimina al cliente de ambos registros al cerrar la conexión.
        Es seguro llamarlo aunque el client_id no exista (idempotente).
        """
        self.active_connections.pop(client_id, None)
        self.response_queues.pop(client_id, None)
        logger.info(f"[WS] Client '{client_id}' disconnected. "
                    f"Total active: {len(self.active_connections)}")

    async def send_to_client(self, client_id: str, message: str):
        """
        Deposita la respuesta del LLM en la cola privada del cliente.

        NOTA: Este método es llamado por process_single_message() en main.py
        cuando el LLM termina. Si el client_id NO existe en active_connections
        (e.g. el mensaje llegó por Telegram o WhatsApp, no por WebSocket),
        simplemente no hace nada — backwards compatible con todos los canales.
        """
        if client_id not in self.response_queues:
            # Mensaje de otro canal (Telegram, WhatsApp, etc.) → ignorar silenciosamente
            return
        await self.response_queues[client_id].put(message)
        logger.info(f"[WS] Response queued for client '{client_id}'.")

    def get_response_queue(self, client_id: str) -> asyncio.Queue:
        """
        Retorna la cola privada de respuesta para que el endpoint WS
        pueda hacer `await queue.get()` y esperar la respuesta del LLM.
        """
        return self.response_queues[client_id]


# Instancia global Singleton — importar en main.py y en el router WS
connection_manager = ConnectionManager()
