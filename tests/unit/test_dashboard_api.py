import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from src.main import app

# Prevent the background agent loop from running during tests
patch("src.main.run_agent_loop", new_callable=AsyncMock).start()

# --- Mocks & Helpers ---

def make_user(full_name="User Test", platform="telegram", platform_user_id="12345"):
    user = MagicMock()
    user.id = 1
    user.full_name = full_name
    user.platform = platform
    user.platform_user_id = platform_user_id
    return user

def make_conversation(conv_id=1, status="handed_off", tenant_id="t1"):
    conv = MagicMock()
    conv.id = conv_id
    conv.status = status
    conv.tenant_id = tenant_id
    conv.user = make_user()
    return conv

# --- Tests ---

@pytest.mark.asyncio
async def test_list_conversations():
    """Verifica el endpoint que lista chats transferidos."""
    mock_convs = [make_conversation(conv_id=10), make_conversation(conv_id=11)]
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        with patch("src.api.routers.dashboard.crud.get_handed_off_conversations", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_convs
            
            headers = {"X-Tenant-ID": "t1"}
            response = await ac.get("/api/dashboard/conversations", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["id"] == 10
            assert data[1]["id"] == 11

@pytest.mark.asyncio
async def test_get_messages():
    """Verifica el endpoint que obtiene el historial de mensajes."""
    msg = MagicMock()
    msg.id = 100
    msg.role = "user"
    msg.content = "Ayuda por favor"
    msg.created_at = "2024-01-01T10:00:00"
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        with patch("src.api.routers.dashboard.crud.get_conversation_messages", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [msg]
            
            headers = {"X-Tenant-ID": "t1"}
            response = await ac.get("/api/dashboard/conversations/1/messages", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["content"] == "Ayuda por favor"

@pytest.mark.asyncio
async def test_reply_to_conversation_telegram():
    """Verifica el envío de respuesta manual via Telegram."""
    conv = make_conversation()
    conv.user.platform = "telegram"
    conv.user.platform_user_id = "54321"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with (
            patch("src.api.routers.dashboard.crud.save_message", new_callable=AsyncMock),
            patch("src.api.routers.dashboard.telegram_responder.send_message", new_callable=AsyncMock) as mock_send,
        ):
            # Mocking the DB execute result for the conversation
            mock_result = MagicMock()
            mock_result.scalars().first.return_value = conv
            
            # Use dependency_overrides for get_db_session
            # ...
            
            # Using a simplified approach to mock the dependency
            with patch("src.api.routers.dashboard.get_db_session") as mock_db_gen:
                mock_session = AsyncMock()
                mock_session.execute.return_value = mock_result
                mock_db_gen.return_value.__aenter__.return_value = mock_session
                
                headers = {"X-Tenant-ID": "t1"}
                response = await ac.post(
                    "/api/dashboard/conversations/1/reply", 
                    json={"content": "Hola, soy tu asesor."},
                    headers=headers
                )
                
                assert response.status_code == 200
                assert response.json()["ok"] is True
                mock_send.assert_awaited_once_with("54321", "Hola, soy tu asesor.")

@pytest.mark.asyncio
async def test_close_conversation():
    """Verifica el cierre de la atención humana (vuelta a bot)."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        with patch("src.api.routers.dashboard.crud.set_conversation_status", new_callable=AsyncMock) as mock_set:
            mock_set.return_value = MagicMock()
            
            headers = {"X-Tenant-ID": "t1"}
            response = await ac.post("/api/dashboard/conversations/1/close", headers=headers)
            
            assert response.status_code == 200
            assert response.json()["status"] == "active"
            mock_set.assert_awaited_once()
