import logging
import os
from typing import Any, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.connection_manager import connection_manager
from src.core.producers.websocket_producer import WebSocketProducer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

# tenant_id para el canal web. Se lee desde el entorno para soportar
# distintos tenants sin redeployar. Definir WEB_CHANNEL_TENANT_ID en .env
WEB_TENANT_ID = os.getenv("WEB_CHANNEL_TENANT_ID", "inasc_web")


@router.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Endpoint WebSocket para el Widget JS del sitio web de INASC.

    Flujo completo por turno de conversación:
    1. Cliente envía JSON: {"text": "...", "user_name": "..."}
    2. WebSocketProducer normaliza y encola en el brain (queue_manager global).
    3. El Agent Loop procesa en background y llama a connection_manager.send_to_client().
    4. Este endpoint recibe la respuesta de su cola privada y la envía al socket.

    Ver ADR completo en implementation_plan.md para el razonamiento de diseño.
    """
    await connection_manager.connect(client_id, websocket)
    producer = WebSocketProducer(tenant_id=WEB_TENANT_ID)
    response_queue = connection_manager.get_response_queue(client_id)

    try:
        while True:
            # 1. Esperar el próximo mensaje del cliente (bloquea asíncronamente)
            data: Dict[str, Any] = await websocket.receive_json()
            logger.info(f"[WS] Message received from client '{client_id}': {str(data)[:80]}")

            # 2. Inyectar el client_id (viene de la URL, no del payload)
            data["client_id"] = client_id

            # 3. Normalizar y enqueue en el brain (retorna de inmediato)
            await producer.enqueue(data)

            # 4. Esperar la respuesta del LLM en la cola privada de este cliente
            #    (bloquea asíncronamente sin congelar el event loop)
            response_text = await response_queue.get()

            # 5. Enviar la respuesta al Widget JS
            await websocket.send_json({
                "role": "agent",
                "content": response_text
            })

    except WebSocketDisconnect:
        logger.info(f"[WS] Client '{client_id}' disconnected gracefully.")
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"[WS] Unexpected error for client '{client_id}': {e}")
        connection_manager.disconnect(client_id)
