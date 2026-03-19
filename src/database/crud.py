from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from src.database.models import User, Conversation, Message, Advisor
from src.models.message import IncomingMessage

async def get_or_create_user(session: AsyncSession, message: IncomingMessage) -> User:
    """
    Finds a user based on tenant_id, platform, and platform_user_id.
    Creates a new user if it does not exist.
    """
    stmt = select(User).where(
        User.tenant_id == message.tenant_id,
        User.platform == message.platform,
        User.platform_user_id == message.platform_user_id
    )
    result = await session.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        user = User(
            tenant_id=message.tenant_id,
            platform=message.platform,
            platform_user_id=message.platform_user_id,
            full_name=message.user_name
        )
        session.add(user)
        await session.flush() # Flush to get the auto-generated ID without committing the transaction yet
    
    return user

async def get_or_create_active_conversation(session: AsyncSession, user_id: int, tenant_id: str) -> Conversation:
    """
    Finds the currently active conversation for a user.
    Creates a new conversation record if none are active.
    """
    stmt = select(Conversation).where(
        Conversation.user_id == user_id,
        Conversation.tenant_id == tenant_id,
        Conversation.status == "active"
    )
    result = await session.execute(stmt)
    conversation = result.scalars().first()
    
    if not conversation:
        conversation = Conversation(
            user_id=user_id,
            tenant_id=tenant_id,
            status="active",
            intent_category="unknown"
        )
        session.add(conversation)
        await session.flush()
        
    return conversation


async def get_latest_conversation(session: AsyncSession, user_id: int, tenant_id: str) -> Optional[Conversation]:
    """
    Retrieves the most recent conversation for a user, regardless of its status.
    Useful for preserving context or detecting handoff states.
    """
    stmt = (
        select(Conversation)
        .where(
            Conversation.user_id == user_id,
            Conversation.tenant_id == tenant_id
        )
        .order_by(desc(Conversation.id))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalars().first()

async def save_message(session: AsyncSession, conversation_id: int, tenant_id: str, role: str, content: str) -> Message:
    """
    Inserts a new message (either user or agent role) into the database.
    Does not commit automatically, so the caller must handle session.commit().
    """
    msg = Message(
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        role=role,
        content=content
    )
    session.add(msg)
    await session.flush()
    return msg

async def get_conversation_history(session: AsyncSession, conversation_id: int, tenant_id: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Retrieves the last N messages for a conversation, formatting them for DeepSeek LLM consumption.
    """
    stmt = select(Message).where(
        Message.conversation_id == conversation_id,
        Message.tenant_id == tenant_id
    ).order_by(desc(Message.id)).limit(limit)
    
    result = await session.execute(stmt)
    messages = result.scalars().all()
    
    # SQLite/MySQL returns unordered iterator when using scalars on reverse logic, so we reverse it manually
    chronological_msgs = reversed(messages)
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in chronological_msgs
    ]


async def get_available_advisor(session: AsyncSession, tenant_id: str) -> Optional[Advisor]:
    """
    Retorna el primer asesor disponible para el tenant dado, o None si no hay ninguno.

    La disponibilidad se controla mediante el campo is_available. En v1 es
    gestionada manualmente (INSERT/UPDATE directo en BD). Versiones futuras
    podrían incluir un endpoint REST para que el asesor cambie su estado.
    """
    stmt = select(Advisor).where(
        Advisor.tenant_id == tenant_id,
        Advisor.is_available == True,
    ).limit(1)
    result = await session.execute(stmt)
    return result.scalars().first()


async def set_conversation_status(session: AsyncSession, conversation_id: int, tenant_id: str, status: str) -> Conversation:
    """
    Cambia el status de una conversación (ej: 'active' → 'handed_off').

    Valores válidos: 'active', 'handed_off', 'pending_callback', 'closed'.
    No hace commit — el caller es responsable de session.commit().
    """
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.tenant_id == tenant_id,
    )
    result = await session.execute(stmt)
    conversation = result.scalars().first()
    if conversation:
        conversation.status = status
        await session.flush()
    return conversation


async def get_handed_off_conversations(session: AsyncSession, tenant_id: str) -> List[Conversation]:
    """
    Retrieves all conversations with 'handed_off' status for a specific tenant.
    Includes the related User object for each conversation.
    """
    from sqlalchemy.orm import joinedload
    stmt = (
        select(Conversation)
        .options(joinedload(Conversation.user))
        .where(
            Conversation.tenant_id == tenant_id,
            Conversation.status == "handed_off"
        )
        .order_by(desc(Conversation.id))
    )
    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def get_conversation_messages(session: AsyncSession, conversation_id: int, tenant_id: str) -> List[Message]:
    """
    Retrieves all messages for a specific conversation in chronological order.
    Used by the Advisor Dashboard to show the full transcript.
    """
    stmt = (
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.tenant_id == tenant_id
        )
        .order_by(Message.id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()
