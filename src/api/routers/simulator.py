from fastapi import APIRouter
from src.core.queue_manager import queue_manager
from src.models.message import IncomingMessage

router = APIRouter(prefix="/simulate", tags=["Testing"])

@router.post("/message")
async def simulate_incoming_message(message: IncomingMessage):
    """
    Simulates a webhook receiving a payload from any channel.
    Notice how this endpoint responds immediately, leaving the actual processing 
    to the background Agent Loop.
    """
    # 1. Empuja a la cola de asyncio
    await queue_manager.enqueue_message(message)
    
    # 2. Responde instantáneamente (HTTP 200 OK)
    return {
        "status": "success", 
        "message": f"Message from {message.platform_user_id} added to the background queue.",
        "queue_size_approx": queue_manager.queue.qsize()
    }
