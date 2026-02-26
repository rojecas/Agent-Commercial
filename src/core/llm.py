import os
import logging
import traceback
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Cargar .env explícitamente aquí porque llm_engine se instancia a nivel
# de módulo (singleton), ANTES de que main.py ejecute su propio load_dotenv().
# Sin este load_dotenv(), os.getenv('DEEPSEEK_API_KEY') retorna None cuando el
# módulo se importa, ya que Python ejecuta el cuerpo del módulo antes de que
# main.py llegue a llamar a su propio load_dotenv().
load_dotenv()

logger = logging.getLogger(__name__)

# Replicamos la logica restrictiva comercial del requerimiento
SYSTEM_PROMPT = """Eres un asistente IA útil, profesional y respetuoso, que trabaja como Asesor Comercial y Soporte Técnico para la empresa Instruments & Applied Sciences S.A.S.- INASC SAS.

REGLAS ESTRICTAS DE COMPORTAMIENTO:
1. Tu conocimiento se limita a la información técnica de los productos que encuentres en el sitio web www.inasc.com.co.
2. Si el usuario te pregunta por temas fuera de contexto (ej. política, historia, cómo programar en Python, etc.), debes declinar educadamente y reconducir la conversación a los productos de INASC.
3. ESTÁ ESTRICTAMENTE PROHIBIDO dar precios. Bajo ninguna circunstancia debes proveer cotizaciones. Informa que para precios deben ser contactados por un especialista a través de ventas@inasc.com.co.
4. Mantén un tono sumamente técnico y conversacional. No seas agresivamente vendedor.
5. Sé conciso: tus respuestas no deberían sobrepasar 2 párrafos cortos (optimizado para móviles). Usa emojis de vez en cuando.
"""

class LLMEngine:
    def __init__(self):
        # Usamos AsyncOpenAI para no bloquear el Event Loop de FastAPI
        api_key = os.getenv("DEEPSEEK_API_KEY", "dummy_key")
        base_url = "https://api.deepseek.com"
        
        # En caso de no tener llave, el cliente arroja error al instanciar sin llave por defecto
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = "deepseek-chat"
        
    async def generate_response(self, context_messages: List[Dict[str, Any]], tenant_id: str = "default") -> str:
        """
        Llama asíncronamente a DeepSeek inyectando el SYSTEM_PROMPT.
        Aísla el contexto usando el tenant_id.
        """
        # FUTURE TODO: Según el 'tenant_id', podemos buscar en la Base de Datos o en Caché (Redis) 
        # un SYSTEM_PROMPT totalmente diferente. Ej: Para InASC actuará como consultor técnico de agua, 
        # pero para "Empresa de Zapatos X" actuará como vendedor de moda, sin sobreescribir variables globales.
        
        dynamic_system_prompt = SYSTEM_PROMPT # Por ahora es igual para todos, luego será dinámico por Tenant
        
        # Asegurarnos de inyectar el System Prompt siempre al principio
        messages = [{"role": "system", "content": dynamic_system_prompt}] + context_messages
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3 # Baja temperatura para respuestas técnicas deterministas
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(
                f"Error communicating with DeepSeek:\n"
                f"  Type   : {type(e).__name__}\n"
                f"  Message: {e}\n"
                f"  Traceback:\n{traceback.format_exc()}"
            )
            return "Lo lamento, en este momento me encuentro experimentando interferencia en mis sistemas centrales. ¿Podría intentarlo de nuevo en unos minutos?"

# Instancia global (Patrón Singleton) a inyectar
llm_engine = LLMEngine()
