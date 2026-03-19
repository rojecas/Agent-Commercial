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
        # tenant_id → List of active advisor WebSockets
        self.active_advisors: dict[str, set[WebSocket]] = {}

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

    # --- Gestión de Asesores (Human Dashboard) ---

    async def connect_advisor(self, tenant_id: str, websocket: WebSocket):
        """
        Registra una ventana de dashboard de un asesor humano.
        """
        await websocket.accept()
        if tenant_id not in self.active_advisors:
            self.active_advisors[tenant_id] = set()
        self.active_advisors[tenant_id].add(websocket)
        logger.info(f"[WS-Advisor] Advisor connected for '{tenant_id}'. Active windows: {len(self.active_advisors[tenant_id])}")

    def disconnect_advisor(self, tenant_id: str, websocket: WebSocket):
        """
        Elimina la ventana del dashboard tras cerrar la conexión.
        """
        if tenant_id in self.active_advisors:
            self.active_advisors[tenant_id].discard(websocket)
            if not self.active_advisors[tenant_id]:
                del self.active_advisors[tenant_id]
        logger.info(f"[WS-Advisor] Advisor disconnected from '{tenant_id}'.")

    async def notify_advisors(self, tenant_id: str, payload: dict):
        """
        Envía una notificación en tiempo real a todas las ventanas
        del dashboard abiertas por asesores de un tenant.
        """
        if tenant_id not in self.active_advisors:
            return

        dead_connections = set()
        for ws in self.active_advisors[tenant_id]:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_connections.add(ws)

        # Cleanup de conexiones muertas
        for ws in dead_connections:
            self.active_advisors[tenant_id].discard(ws)


# Instancia global Singleton — importar en main.py y en el router WS
connection_manager = ConnectionManager()
