import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.core.llm import LLMEngine, SYSTEM_PROMPT

@pytest.fixture
def llm_engine(monkeypatch):
    """
    Fixture que inyecta una llave falsa de API y devuelve la instancia del LLM.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key_123")
    return LLMEngine()

@pytest.mark.asyncio
async def test_generate_response_success(llm_engine):
    """
    Testea que la llamada a la API devuelve el texto correctamente mockeado
    """
    with patch.object(llm_engine.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        
        # Simulamos la respuesta estructurada de OpenAI
        mock_message = MagicMock()
        mock_message.content = "Hola, soy el asistente."
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # El AsyncMock devuelve el objeto mock_response
        mock_create.return_value = mock_response
        
        # Llamamos al motor
        input_messages = [{"role": "user", "content": "Hola"}]
        result = await llm_engine.generate_response(input_messages)
        
        # Verificamos
        assert result == "Hola, soy el asistente."
        
        # Verificamos que el system prompt se inyectó correctamente
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        
        assert call_args['model'] == "deepseek-chat"
        assert len(call_args['messages']) == 2
        assert call_args['messages'][0]['role'] == "system"
        assert call_args['messages'][0]['content'] == SYSTEM_PROMPT
        assert call_args['messages'][1]['role'] == "user"

@pytest.mark.asyncio
async def test_generate_response_exception(llm_engine):
    """
    Testea el bloque de fallback si la API de DeepSeek arroja timeout/error
    """
    with patch.object(llm_engine.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("Connection Timeout")
        
        result = await llm_engine.generate_response([{"role": "user", "content": "Hola"}], tenant_id="inasc_1")
        
        assert "interferencia en mis sistemas centrales" in result
