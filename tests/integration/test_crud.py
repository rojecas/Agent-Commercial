import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.database.base import Base
from src.database.models import Company, CompanyDivision, User, Conversation, Message
from src.database.crud import get_or_create_user, get_or_create_active_conversation, save_message, get_conversation_history
from src.models.message import IncomingMessage

# Use MariaDB for testing to exactly match the production dialect.
# Requires 'comm_agent_test' database to exist.
TEST_DATABASE_URL = "mysql+aiomysql://root:@127.0.0.1:3306/comm_agent_test"

@pytest_asyncio.fixture
async def async_db_session():
    """
    Creates fresh tables in the test database and yields an AsyncSession.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )
    
    # Clean up any leftover tables from a previous crashed run, then freshly create them
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine, class_=AsyncSession)
    
    async with TestingSessionLocal() as session:
        yield session
        
    # Drop all tables after the test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_and_link_b2b_hierarchy(async_db_session: AsyncSession):
    """
    Tests that a Company, Division, and User can be manually created and linked correctly.
    """
    tenant = "test_tenant"
    
    # 1. Create Company
    company = Company(name="Ingenio del Cauca", tenant_id=tenant, crm_company_id="CRM-COMP-001")
    async_db_session.add(company)
    await async_db_session.flush()
    
    # 2. Create Division
    division = CompanyDivision(name="Laboratorio de Aguas", company_id=company.id, tenant_id=tenant, crm_division_id="CRM-DIV-001")
    async_db_session.add(division)
    await async_db_session.flush()
    
    # 3. Create User in that division
    user = User(
        full_name="Don Raul",
        platform="whatsapp",
        platform_user_id="+573000000001",
        division_id=division.id,
        tenant_id=tenant,
        crm_contact_id="CRM-CONT-001"
    )
    async_db_session.add(user)
    await async_db_session.commit()
    
    # Verify the IDs were generated and foreign keys match
    assert company.id is not None
    assert division.company_id == company.id
    assert user.division_id == division.id
    assert user.crm_contact_id == "CRM-CONT-001"

@pytest.mark.asyncio
async def test_crud_chat_flow(async_db_session: AsyncSession):
    """
    Simulates the Flow of Issue #3: User arrives, conversation starts, messages are saved and retrieved.
    """
    # 1. Arrives an incoming message
    incoming = IncomingMessage(
        platform="whatsapp",
        platform_user_id="+5712345678",
        tenant_id="client_x",
        content="Hola, tengo problemas con el cloro.",
        user_name="María"
    )
    
    # 2. Test user creation/retrieval
    user = await get_or_create_user(async_db_session, incoming)
    assert user.full_name == "María"
    assert user.platform_user_id == "+5712345678"
    assert user.id is not None
    
    # 3. Test active conversation logic
    convo = await get_or_create_active_conversation(async_db_session, user.id, "client_x")
    assert convo.status == "active"
    assert convo.user_id == user.id
    
    # 4. Save User Message
    await save_message(async_db_session, convo.id, "client_x", "user", incoming.content)
    
    # 5. Save Agent Response
    await save_message(async_db_session, convo.id, "client_x", "assistant", "¡Hola María! ¿En qué puedo ayudarte con el cloro?")
    
    await async_db_session.commit()
    
    # 6. Test History Retrieval
    history = await get_conversation_history(async_db_session, convo.id, "client_x", limit=10)
    
    # Assert chronology: user should be first, assistant second.
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert "problemas con el cloro" in history[0]["content"]
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "¡Hola María! ¿En qué puedo ayudarte con el cloro?"
