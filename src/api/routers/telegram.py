import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request

from src.core.producers.telegram_producer import TelegramProducer, TELEGRAM_TENANT_ID

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Telegram"])

# Token secreto opcional para validar que los POSTs vienen realmente de Telegram.
# Configurar en .env como TELEGRAM_WEBHOOK_SECRET.
# Si no está definido, el endpoint acepta todos los requests (modo desarrollo).
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")


@router.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(default=""),
):
    """
    Endpoint que recibe los updates de Telegram via Webhook (push).

    Flujo por cada update recibido:
    1. Validar el token secreto (si TELEGRAM_WEBHOOK_SECRET está definido).
    2. Parsear el body JSON del update.
    3. Si no tiene 'message.text' → ignorar (fotos, stickers, comandos, etc.).
    4. TelegramProducer normaliza el payload → IncomingMessage → Queue.
    5. Responder 200 OK inmediatamente (Telegram requiere < 60s o reintenta).

    IMPORTANTE: La respuesta al usuario se envía de forma asíncrona por
    TelegramResponder en process_single_message(), NO en este endpoint.
    """
    # --- 1. Validación del token secreto (skip si no está configurado) ---
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        logger.warning(
            "[TelegramWebhook] Token secreto inválido. Request rechazado."
        )
        raise HTTPException(status_code=403, detail="Invalid secret token")

    # --- 2. Parsear el body ---
    try:
        update: Dict[str, Any] = await request.json()
    except Exception:
        logger.warning("[TelegramWebhook] Body JSON inválido.")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    logger.info(f"[TelegramWebhook] Update recibido: update_id={update.get('update_id')}")

    # --- 3. Ignorar updates sin 'message.text' ---
    message = update.get("message", {})
    if not message.get("text"):
        logger.info("[TelegramWebhook] Update sin texto (foto, sticker, etc.) — ignorado.")
        return {"ok": True}

    # --- 4. Normalizar y enqueue ---
    producer = TelegramProducer(tenant_id=TELEGRAM_TENANT_ID)
    try:
        await producer.enqueue(update)
    except ValueError as e:
        # process_payload puede levantar ValueError para updates sin texto
        logger.info(f"[TelegramWebhook] Update descartado: {e}")

    # --- 5. Responder 200 inmediatamente ---
    return {"ok": True}
