from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List
from pydantic import BaseModel
import logging

from src.database.connection import get_db_session
from src.database import crud
from src.database.models import Conversation
from src.core.whatsapp_responder import whatsapp_responder
from src.core.telegram_responder import telegram_responder
from src.core.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

class ReplyRequest(BaseModel):
    content: str

@router.get("/conversations")
async def list_conversations(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db_session)
):
    conversations = await crud.get_handed_off_conversations(db, x_tenant_id)
    return [
        {
            "id": conv.id,
            "status": conv.status,
            "user": {
                "id": conv.user.id,
                "full_name": conv.user.full_name,
                "platform": conv.user.platform,
                "platform_user_id": conv.user.platform_user_id
            }
        }
        for conv in conversations
    ]

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db_session)
):
    messages = await crud.get_conversation_messages(db, conversation_id, x_tenant_id)
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at
        }
        for msg in messages
    ]

@router.post("/conversations/{conversation_id}/reply")
async def reply_to_conversation(
    conversation_id: int,
    request: ReplyRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db_session)
):
    # 1. Fetch conversation with user details
    stmt = (
        select(Conversation)
        .options(joinedload(Conversation.user))
        .where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == x_tenant_id
        )
    )
    result = await db.execute(stmt)
    conversation = result.scalars().first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Routing response to the correct channel
    platform = conversation.user.platform
    recipient_id = conversation.user.platform_user_id
    success = False

    try:
        if platform == "telegram":
            success = await telegram_responder.send_message(recipient_id, request.content)
        elif platform == "whatsapp":
            success = await whatsapp_responder.send_message(recipient_id, request.content)
        elif platform == "web":
            await connection_manager.send_to_client(recipient_id, request.content)
            success = True
        else:
            logger.error(f"[Dashboard] Unsupported platform: {platform}")
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

        if not success and platform in ("telegram", "whatsapp"):
             # For some reason the responder failed (e.g. invalid token)
             # In dev mode we might want to allow saving to DB anyway to test the flow
             logger.warning(f"[Dashboard] Responder failed for {platform}. Saving to DB anyway for audit.")

        # 3. Save message to DB as assistant
        await crud.save_message(
            db, 
            conversation_id=conversation.id, 
            tenant_id=x_tenant_id, 
            role="assistant", 
            content=request.content
        )
        await db.commit()

        return {"ok": True, "success": success}

    except Exception as e:
        logger.error(f"[Dashboard] Error replying to conversation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: int,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db_session)
):
    conversation = await crud.set_conversation_status(db, conversation_id, x_tenant_id, "active")
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.commit()
    return {"ok": True, "status": "active"}
