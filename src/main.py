import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from src.core.queue_manager import queue_manager

# Setup environment variables configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            
            # FUTURE TODO: 
            # 2. Retrieve Conversation Context from DB
            # 3. Call LLM (DeepSeek)
            # 4. Extract Tools/Skills
            # 5. Route Response back to the Producer's send method
            
            # Simulate intense LLM processing time for the dummy version
            logger.info(f"🤔 Thinking about message: '{message.content}'...")
            await asyncio.sleep(2)
            
            logger.info(f"✅ Finished processing message from {message.platform_user_id}")
            
        except asyncio.CancelledError:
            logger.warning("Agent Loop was cancelled. Shutting down brain safely.")
            break
        except Exception as e:
            logger.error(f"Error in Agent Loop: {e}")
        finally:
            queue_manager.mark_task_done()

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
    version="1.1.0",
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
