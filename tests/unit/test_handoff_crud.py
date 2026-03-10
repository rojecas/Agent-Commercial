"""
Tests unitarios para las funciones CRUD de handoff — Issue #23.

Testea get_available_advisor() y set_conversation_status()
usando mocks de la sesión de SQLAlchemy.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Tests get_available_advisor ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_available_advisor_found():
    """Retorna el primer asesor con is_available=True del tenant."""
    from src.database.crud import get_available_advisor

    advisor = MagicMock()
    advisor.name = "Carlos Pérez"
    advisor.is_available = True

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = advisor

    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)

    result = await get_available_advisor(session, "inasc_001")
    assert result is advisor
    assert result.name == "Carlos Pérez"


@pytest.mark.asyncio
async def test_get_available_advisor_none():
    """Retorna None cuando no hay asesores disponibles."""
    from src.database.crud import get_available_advisor

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None

    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)

    result = await get_available_advisor(session, "inasc_001")
    assert result is None


# ── Tests set_conversation_status ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_conversation_status():
    """Cambia el status de la conversación y hace flush."""
    from src.database.crud import set_conversation_status

    conversation = MagicMock()
    conversation.status = "active"

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = conversation

    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)

    result = await set_conversation_status(session, conversation_id=1, tenant_id="inasc_001", status="handed_off")


    assert result.status == "handed_off"
    session.flush.assert_awaited_once()
