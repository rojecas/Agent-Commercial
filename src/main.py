import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from src.core.queue_manager import queue_manager
from src.core.connection_manager import connection_manager
from src.core.telegram_responder import telegram_responder
from src.core.llm import llm_engine
from src.database.connection import async_session_factory
from src.database import crud

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
        # Abrimos Sesión de BD por Transacción
        async with async_session_factory() as session:
            # 2. Recuperar el contexto de la BD cruzando Tenant y Usuario
            user = await crud.get_or_create_user(session, message)
            conversation = await crud.get_or_create_active_conversation(session, user.id, message.tenant_id)
            
            # Guardamos el mensaje entrante del prospecto
            await crud.save_message(session, conversation.id, message.tenant_id, role="user", content=message.content)
            
            # Recuperamos el historial de memoria dinámico (Últimos 10 mensajes)
            context = await crud.get_conversation_history(session, conversation.id, message.tenant_id, limit=10)
            
            # 3. Call LLM (DeepSeek)
            logger.info(f"[{message.tenant_id}] 🤔 Thinking about message from {message.platform_user_id}: '{message.content}'...")
            
            # Llamada Asíncrona al Motor LLM
            response_text = await llm_engine.generate_response(context, tenant_id=message.tenant_id)
            
            # 4. Guardar la respuesta generada por el agente en la base de datos
            await crud.save_message(session, conversation.id, message.tenant_id, role="assistant", content=response_text)
            
            # 5. ¡Commit! Guardamos todo permanentemente en MySQL si ocurrió sin errores
            await session.commit()
            
            logger.info(f"[{message.tenant_id}] ✅ Finished and saved to DB. LLM Response: {response_text[:50]}...")
            
        from src.models.message import AgentResponse
        agent_response = AgentResponse(
            recipient_id=message.platform_user_id,
            content=response_text
        )
        logger.info(f"[{message.tenant_id}] 📤 Routing response to '{message.platform}' channel for '{message.platform_user_id}'")

        # Ruteo de respuesta al canal de origen.
        # Canal web (WebSocket): deposita la respuesta en la cola privada asyncio del cliente.
        # Canal telegram:        llama sendMessage de la API de Telegram de forma asíncrona.
        # Otros canales futuros: añadir elif aquí (WhatsApp, Signal, etc.)
        if message.platform == "telegram":
            await telegram_responder.send_message(message.platform_user_id, response_text)
        else:
            # Fallback para WebSocket y futuros canales con cola asyncio
            await connection_manager.send_to_client(message.platform_user_id, response_text)
        
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
    # Cerrar el cliente HTTP de TelegramResponder limpiamente
    await telegram_responder.close()

# Initialize FastAPI with the lifespan context manager
app = FastAPI(
    title="INASC Commercial Agent API",
    description="Multi-Tenant Async Brain for Conversational Sales",
    version="Beta 1.0.0",
    lifespan=lifespan
)

# Import and mount our routers
from src.api.routers import simulator
from src.api.routers import websocket
from src.api.routers import telegram
app.include_router(simulator.router)
app.include_router(websocket.router)
app.include_router(telegram.router)

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
