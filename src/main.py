from fastapi import FastAPI
import os

app = FastAPI(
    title="INASC Agent Backend",
    description="Microservicio 24/7 para el Agente Comercial Multicanal",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "INASC Conversational Agent",
        "environment": os.getenv("APP_STATUS", "unknown")
    }

# Aquí posteriormente registraremos los routers (Webhooks de Telegram, WhatsApp, y WebSockets)
# app.include_router(telegram_router, prefix="/api/webhook")
