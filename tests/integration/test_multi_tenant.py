"""
Test de integración: simulación multi-tenant.

Verifica que dos empresas (tenants) distintas usando la misma instancia
del servidor no mezclan sus datos. Cada tenant tiene su propio usuario,
conversación e historial de mensajes completamente aislados.

Contexto arquitectónico:
- tenant_id representa la EMPRESA (e.g., "empresa_a", "empresa_b")
- platform distingue el canal ('telegram', 'web')
- Un mismo usuario de "empresa_a" jamás debe ver datos de "empresa_b"
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from src.database.base import Base
from src.database import crud
from src.models.message import IncomingMessage

pytestmark = pytest.mark.asyncio

# ─────────────────────────────────────────────
# Fixture: base de datos de test aislada
# ─────────────────────────────────────────────
TEST_DB_URL = "mysql+aiomysql://root:@127.0.0.1:3306/comm_agent_test"


@pytest_asyncio.fixture
async def test_engine():
    """Engine con lifecycle completo por test — garantiza aislamiento de event loop."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Sesión limpia por test — rollback automático al finalizar."""
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def make_message(platform_user_id: str, tenant_id: str, content: str, platform: str = "web") -> IncomingMessage:
    return IncomingMessage(
        platform=platform,
        platform_user_id=platform_user_id,
        tenant_id=tenant_id,
        content=content,
        user_name=f"User_{platform_user_id}",
    )


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────
class TestMultiTenantIsolation:

    @pytest.mark.asyncio
    async def test_dos_tenants_crean_usuarios_independientes(self, db_session: AsyncSession):
        """Dos tenants con el mismo platform_user_id generan usuarios distintos en BD."""
        msg_a = make_message(platform_user_id="user_99", tenant_id="empresa_a", content="Hola desde A")
        msg_b = make_message(platform_user_id="user_99", tenant_id="empresa_b", content="Hola desde B")

        user_a = await crud.get_or_create_user(db_session, msg_a)
        await db_session.commit()

        user_b = await crud.get_or_create_user(db_session, msg_b)
        await db_session.commit()

        # Mismo platform_user_id pero diferente tenant → deben ser usuarios distintos
        assert user_a.id != user_b.id
        assert user_a.tenant_id == "empresa_a"
        assert user_b.tenant_id == "empresa_b"

    @pytest.mark.asyncio
    async def test_conversaciones_de_tenants_no_se_mezclan(self, db_session: AsyncSession):
        """Cada tenant tiene su propia conversación aislada."""
        msg_a = make_message("user_88", "empresa_a", "Consulta de empresa A")
        msg_b = make_message("user_88", "empresa_b", "Consulta de empresa B")

        user_a = await crud.get_or_create_user(db_session, msg_a)
        conv_a = await crud.get_or_create_active_conversation(db_session, user_a.id, "empresa_a")
        await db_session.commit()

        user_b = await crud.get_or_create_user(db_session, msg_b)
        conv_b = await crud.get_or_create_active_conversation(db_session, user_b.id, "empresa_b")
        await db_session.commit()

        assert conv_a.id != conv_b.id
        assert conv_a.tenant_id == "empresa_a"
        assert conv_b.tenant_id == "empresa_b"

    @pytest.mark.asyncio
    async def test_historial_de_mensajes_aislado_por_tenant(self, db_session: AsyncSession):
        """El historial de un tenant no contiene mensajes del otro tenant."""
        # Tenant A: 2 mensajes
        msg_a = make_message("user_77", "empresa_a", "Primer mensaje A")
        user_a = await crud.get_or_create_user(db_session, msg_a)
        conv_a = await crud.get_or_create_active_conversation(db_session, user_a.id, "empresa_a")
        await crud.save_message(db_session, conv_a.id, "empresa_a", role="user", content="Primer mensaje A")
        await crud.save_message(db_session, conv_a.id, "empresa_a", role="assistant", content="Respuesta A")
        await db_session.commit()

        # Tenant B: 1 mensaje
        msg_b = make_message("user_77", "empresa_b", "Mensaje empresa B")
        user_b = await crud.get_or_create_user(db_session, msg_b)
        conv_b = await crud.get_or_create_active_conversation(db_session, user_b.id, "empresa_b")
        await crud.save_message(db_session, conv_b.id, "empresa_b", role="user", content="Mensaje empresa B")
        await db_session.commit()

        # Recuperar historial de cada tenant
        history_a = await crud.get_conversation_history(db_session, conv_a.id, "empresa_a")
        history_b = await crud.get_conversation_history(db_session, conv_b.id, "empresa_b")

        # Verificar aislamiento
        assert len(history_a) == 2
        assert len(history_b) == 1

        contents_a = [m["content"] for m in history_a]
        contents_b = [m["content"] for m in history_b]

        assert "Mensaje empresa B" not in contents_a
        assert "Primer mensaje A" not in contents_b
        assert "Respuesta A" not in contents_b

    @pytest.mark.asyncio
    async def test_mismo_tenant_distintos_canales_mismo_usuario(self, db_session: AsyncSession):
        """
        Un mismo tenant con distintos canales (platform) genera usuarios distintos.
        Esto es correcto: un contacto por Telegram y uno por Web son entidades distintas
        hasta que el sistema los vincule (funcionalidad futura de deduplicación).
        """
        msg_web = make_message("user_66", "empresa_a", "Hola desde web", platform="web")
        msg_tg  = make_message("user_66", "empresa_a", "Hola desde telegram", platform="telegram")

        user_web = await crud.get_or_create_user(db_session, msg_web)
        await db_session.commit()

        user_tg = await crud.get_or_create_user(db_session, msg_tg)
        await db_session.commit()

        # Mismo tenant_id y platform_user_id pero diferente platform → usuarios distintos
        assert user_web.id != user_tg.id
        assert user_web.platform == "web"
        assert user_tg.platform == "telegram"
        assert user_web.tenant_id == user_tg.tenant_id == "empresa_a"
