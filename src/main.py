import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from src.core.queue_manager import queue_manager
from src.core.llm import llm_engine

# Setup environment variables configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_single_message(message):
    """
    Worker individual que procesa el mensaje de UNA sola conversación concurrente.
    Al crearse como una Task independiente de Asyncio, Aisla totalmente a un Tenant de otro o
    a un Prospecto A de un Prospecto B.
    """
    try:
        # FUTURE TODO: 
        # 2. Retrieve Conversation Context from DB using BOTH message.tenant_id and message.platform_user_id
        
        # 3. Call LLM (DeepSeek)
        logger.info(f"[{message.tenant_id}] 🤔 Thinking about message from {message.platform_user_id}: '{message.content}'...")
        
        # Formateamos el historial simulado por ahora (Issue #3 integrará a la BD)
        context = [{"role": "user", "content": message.content}]
        
        # Llamada Asíncrona al Motor LLM. Pasamos el tenant_id para que el motor cargue el prompt adecuado
        response_text = await llm_engine.generate_response(context, tenant_id=message.tenant_id)
        
        logger.info(f"[{message.tenant_id}] ✅ Finished processing message. LLM Response: {response_text[:50]}...")
        
        # 4. Extract Tools/Skills (FUTURE TODO)
        
        # 5. Route Response back to the Producer's send method (FUTURE TODO)
        from src.models.message import AgentResponse
        agent_response = AgentResponse(
            recipient_id=message.platform_user_id,
            content=response_text
        )
        logger.info(f"[{message.tenant_id}] 📤 Prepared Response Object to be routed: {agent_response.model_dump()}")
        
    except Exception as e:
        logger.error(f"[{message.tenant_id}] Error in worker processing message: {e}")
    finally:
        # Siempre marcar la tarea principal de la cola como hecha
        queue_manager.mark_task_done()

async def run_agent_loop():
    """
    This is the Core Orchestrator Loop.
    It runs perpetually in the background, fully detached from incoming web requests.
    """
    logger.info("🧠 Brain Initialized: Async Agent Loop started.")
    
    while True:
        try:
            # 1. Blocks here WITHOUT freezing the API until a new message arrives from any channel
            message = await queue_manager.get_message()
            logger.info(f"📥 Agent picked up message from: {message.platform_user_id} on {message.platform}")
            
            # Lanzamos una tarea de Background (Worker Concurrente) y seguimos vaciando el buzón INMEDIATAMENTE
            asyncio.create_task(process_single_message(message))
            
        except asyncio.CancelledError:
            logger.warning("Agent Loop was cancelled. Shutting down brain safely.")
            break
        except Exception as e:
            logger.error(f"Error in Orchestrator Loop: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch the perpetual background Agent loop
    agent_task = asyncio.create_task(run_agent_loop())
    
    yield # API is running and accepting requests here
    
    # Shutdown: Cancel the loop gracefully
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass

# Initialize FastAPI with the lifespan context manager
app = FastAPI(
    title="INASC Commercial Agent API",
    description="Multi-Tenant Async Brain for Conversational Sales",
    version="Beta 1.0.0",
    lifespan=lifespan
)

# Import and mount our routers
from src.api.routers import simulator
app.include_router(simulator.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "INASC Conversational Agent",
    }

@app.get("/health")
async def health_check():
    """
    Simple check to see if the API and Queue are alive.
    """
    return {
        "status": "healthy",
        "queue_size": queue_manager.queue.qsize()
    }
