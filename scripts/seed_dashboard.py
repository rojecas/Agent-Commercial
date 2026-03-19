import asyncio
import sys
import os

# Asegurar que el path sea correcto para importar desde src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import async_session_factory
from src.database.models import User, Conversation, Message

async def seed():
    print("🌱 Iniciando seeding simplificado...")
    
    mocks = [
        {"name": "Juan Perez", "uid": "wa_111", "plat": "whatsapp", "text": "Cotizacion de pHmetros"},
        {"name": "Maria Garcia", "uid": "tg_222", "plat": "telegram", "text": "Duda sobre garantia"},
        {"name": "Carlos Ruiz", "uid": "web_333", "plat": "web", "text": "Stock de sensores"}
    ]

    async with async_session_factory() as session:
        try:
            for m in mocks:
                print(f"-> Mocking: {m['name']}...")
                
                # 1. Crear Usuario
                user = User(
                    full_name=m['name'],
                    platform=m['plat'],
                    platform_user_id=m['uid'],
                    tenant_id="inasc_001"
                )
                session.add(user)
                await session.flush()

                # 2. Crear Conversación (handed_off)
                conv = Conversation(
                    user_id=user.id,
                    status="handed_off",
                    tenant_id="inasc_001",
                    intent_category="sales"
                )
                session.add(conv)
                await session.flush()

                # 3. Guardar Mensaje
                msg = Message(
                    conversation_id=conv.id,
                    tenant_id="inasc_001",
                    role="user",
                    content=m['text']
                )
                session.add(msg)

            await session.commit()
            print("\n✅ [SUCCESS] Datos insertados correctamente.")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ [ERROR] Error de base de datos: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(seed())
