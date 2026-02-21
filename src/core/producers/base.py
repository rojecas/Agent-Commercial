from abc import ABC, abstractmethod
from typing import Any
from src.models.message import IncomingMessage
from src.core.queue_manager import queue_manager

class BaseProducer(ABC):
    """
    Abstract Base Class for all channel producers.
    A producer is responsible for:
    1. Receiving the raw payload from a specific platform.
    2. Normalizing it into the standard `IncomingMessage` format.
    3. Pushing it into the asynchronous Queue.
    """
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    @abstractmethod
    async def process_payload(self, raw_payload: Any) -> IncomingMessage:
        """
        Takes the raw webhook JSON from the specific platform and returns
        a normalized IncomingMessage object.
        Must be implemented by child classes (e.g. TelegramProducer).
        """
        pass

    async def enqueue(self, raw_payload: Any):
        """
        Core flow: Normalizes the payload and pushes it to the asyncio queue.
        This is the method the FastAPI endpoints will typically call.
        """
        standard_message = await self.process_payload(raw_payload)
        
        # Inyecta el tenant_id configurado para esta instancia de productor
        if not standard_message.tenant_id:
             standard_message.tenant_id = self.tenant_id
             
        await queue_manager.enqueue_message(standard_message)
        return {"status": "enqueued", "id": standard_message.platform_user_id}
