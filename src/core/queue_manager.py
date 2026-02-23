import asyncio
import logging
from src.models.message import IncomingMessage

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageQueueManager:
    """
    A Singleton queue manager that decouples the fast webhook ingestion (FastAPI)
    from the slow LLM processing (Core Engine).
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessageQueueManager, cls).__new__(cls)
            # Inicializar la cola de asyncio. 
            # maxsize=0 significa infinita, aunque en prod podría limitarse para evitar OOM.
            cls._instance.queue = asyncio.Queue()
        return cls._instance

    async def enqueue_message(self, message: IncomingMessage):
        """
        Push a new message into the processing queue.
        This is called by the FastAPI endpoints instantly.
        """
        await self.queue.put(message)
        logger.info(f"Message from {message.platform_user_id} stacked. Queue size approximate: {self.queue.qsize()}")

    async def get_message(self) -> IncomingMessage:
        """
        Pull the next message from the queue.
        This blocks asynchronously until a message is available.
        """
        return await self.queue.get()

    def mark_task_done(self):
        """
        Acknowledge that the message has been fully processed by the LLM.
        """
        self.queue.task_done()
        
# Instancia global para ser importada en toda la app
queue_manager = MessageQueueManager()
