import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, Request

from src.core.producers.whatsapp_producer import WhatsAppProducer, TENANT_ID as WA_TENANT_ID

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WhatsApp"])

# Token de verificación que Meta usa para validar el webhook.
# Debe coincidir con el valor configurado en el Meta Developer Dashboard.
# Definir WHATSAPP_VERIFY_TOKEN en .env antes de registrar el webhook.
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "inasc_whatsapp_verify_token")


@router.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    """
    Endpoint de verificación del webhook — requerido por Meta.

    Cuando registras el webhook en el Meta Developer Dashboard, Meta
    envía un GET con estos parámetros para confirmar que el servidor
    es el tuyo. El servidor debe responder con el hub.challenge como
    texto plano (sin comillas, sin JSON).

    Meta envía:
        GET /webhook/whatsapp
            ?hub.mode=subscribe
            &hub.verify_token=TU_TOKEN
            &hub.challenge=RETO_ALEATORIO

    Respuesta esperada: el reto exacto como texto plano.
    """
    logger.info(
        f"[WhatsApp] Solicitud de verificación de webhook — "
        f"mode={hub_mode}, token_match={hub_verify_token == VERIFY_TOKEN}"
    )

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("[WhatsApp] ✅ Webhook verificado exitosamente por Meta.")
        # Meta requiere texto plano, NO JSON — respondemos el challenge directo
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=hub_challenge, status_code=200)

    logger.warning(
        "[WhatsApp] ❌ Verificación de webhook fallida. "
        f"Token recibido: '{hub_verify_token}' | Token esperado: '{VERIFY_TOKEN}'"
    )
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook_receive(request: Request):
    """
    Endpoint que recibe los mensajes entrantes de WhatsApp via Meta webhook.

    Flujo por cada update recibido:
    1. Parsear el body JSON del update de Meta.
    2. Verificar que contiene mensajes de texto (ignorar otros tipos).
    3. WhatsAppProducer normaliza payload → IncomingMessage → Queue.
    4. Responder 200 OK inmediatamente.
       (Meta reintenta si no recibe 200 en < 20s)

    IMPORTANTE: La respuesta al usuario se envía de forma asíncrona por
    WhatsAppResponder en process_single_message() de main.py,
    NO en este endpoint — mismo patrón que Telegram.
    """
    # --- 1. Parsear el body ---
    try:
        update: Dict[str, Any] = await request.json()
    except Exception:
        logger.warning("[WhatsApp] Body JSON inválido.")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    logger.info(f"[WhatsApp] Update recibido: object={update.get('object')}")

    # --- 2. Filtro rápido: ignorar notificaciones que no sean mensajes ---
    # Meta también envía updates de estado (delivered, read) que no son mensajes
    try:
        entry = update.get("entry", [{}])[0]
        change = entry.get("changes", [{}])[0].get("value", {})
        if not change.get("messages"):
            logger.info("[WhatsApp] Update sin mensajes (status update) — ignorado.")
            return {"ok": True}
    except (IndexError, KeyError):
        logger.info("[WhatsApp] Update sin estructura de mensajes — ignorado.")
        return {"ok": True}

    # --- 3. Normalizar y enqueue ---
    producer = WhatsAppProducer(tenant_id=WA_TENANT_ID)
    try:
        await producer.enqueue(update)
    except ValueError as e:
        # process_payload levanta ValueError para mensajes no-texto (fotos, audio)
        logger.info(f"[WhatsApp] Mensaje descartado: {e}")

    # --- 4. Responder 200 inmediatamente (Meta requiere < 20s) ---
    return {"ok": True}
