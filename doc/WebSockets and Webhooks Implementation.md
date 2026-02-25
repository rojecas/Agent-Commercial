##  Registro de Decisi��n Arquitect��nica (ADR)
**NOTE:** Esta sección documenta el razonamiento detrás del diseño elegido. Fue redactada antes de escribir código para preservar el contexto de las decisiones tomadas en la sesión de diseño del 2026-02-23.

El Problema Central de este Issue
Implementar WebSockets en FastAPI es trivial. El reto real es el siguiente: ¿cómo le regresa la respuesta del LLM al socket del cliente que la originó?

El motivo por el que esto no es obvio radica en la arquitectura existente:
```
[ENDPOINT WS]  �? encola mensaje  �? [QUEUE GLOBAL]  �? [AGENT LOOP]
     �?                                                       �?
     |                                                   genera respuesta
     |                                                        �?
     |_____________ ??? ¿Cómo regresa aquí? _________________|
```
El run_agent_loop() y process_single_message() corren como tareas de asyncio completamente desacopladas del endpoint FastAPI. Cuando el LLM termina, no existe ningún mecanismo automático para saber a qué socket devolver la respuesta.

### Opciones Evaluadas
**Opción A** �?ConnectionManager Singleton con Cola Privada por Cliente �?(ELEGIDA)
Cómo funciona:

Se crea una clase ConnectionManager como singleton global (exactamente igual a como queue_manager ya es un singleton).
Al conectarse un cliente WebSocket, se registra en un diccionario {client_id �?WebSocket} y se crea una asyncio.Queue() privada para ese cliente: {client_id �?Queue}.
El endpoint WS espera mensajes del cliente, los encola en el brain, y luego se queda bloqueado asíncronamente en await response_queue.get() �?sin congelar el event loop.
Cuando 
process_single_message()
 termina, llama a connection_manager.send_to_client(client_id, texto), que deposita la respuesta en la 
Queue
 privada de ese cliente.
El endpoint WS se desbloquea, recibe la respuesta y la envía al socket.
Por qué es correcta:

Cada client_id tiene su propia 
Queue
 aislada. Imposible que la respuesta del Prospecto A llegue al Prospecto B.
Es el patrón estándar de la industria para este problema (es lo que Socket.IO usa internamente).
Es completamente aditiva: no modifica la lógica existente del queue global.
Opción B �?Referencia al Socket/Queue dentro de 
IncomingMessage
Cómo funcionaría:

Se añade un campo response_queue: Optional[asyncio.Queue] al modelo 
IncomingMessage
.
El endpoint WS inyecta su cola directamente en el mensaje antes de encolarlo.
process_single_message()
 deposita la respuesta en message.response_queue.
Por qué fue descartada:

IncomingMessage
 es un modelo Pydantic de dominio �?representa un mensaje de negocio, no una transacción de red. Contaminarla con objetos de infraestructura (asyncio.Queue, WebSocket) viola el principio de separación de responsabilidades.
Pydantic no puede serializar ni validar asyncio.Queue. Habría que declararlo como Any, perdiendo toda la tipificación y la documentación automática de la API.
Para mensajes de Telegram/WhatsApp (que no tienen socket), el campo siempre estaría en None, haciendo el modelo inconsistente.
Escenario Validado: 5 Prospectos Concurrentes, 2 Tenants
Este fue el escenario clave que validó la decisión. Supón:

Tenant #1 (Laboratorio Metrológico): Prospecto_A y Prospecto_B conectados por WebSocket.
Tenant #2 (Minorista de Zapatos): Prospecto_C, Prospecto_D y Prospecto_E conectados por WebSocket.
Estado en memoria del ConnectionManager:

python
active_connections = {
    "prospecto_A": <WebSocket>,  # Tenant#1
    "prospecto_B": <WebSocket>,  # Tenant#1
    "prospecto_C": <WebSocket>,  # Tenant#2
    "prospecto_D": <WebSocket>,  # Tenant#2
    "prospecto_E": <WebSocket>,  # Tenant#2
}
response_queues = {
    "prospecto_A": asyncio.Queue(),  # Solo recibe SU respuesta
    "prospecto_B": asyncio.Queue(),  # Solo recibe SU respuesta
    "prospecto_C": asyncio.Queue(),  # Solo recibe SU respuesta
    "prospecto_D": asyncio.Queue(),  # Solo recibe SU respuesta
    "prospecto_E": asyncio.Queue(),  # Solo recibe SU respuesta
}
Flujo cuando los 5 escriben casi simultáneo (t=0):

t=0.00s  Prospecto_A envía �?encolado (tenant_id="lab_metro")
t=0.01s  Prospecto_C envía �?encolado (tenant_id="zapatos")
t=0.02s  Prospecto_B envía �?encolado (tenant_id="lab_metro")
... etc.
run_agent_loop() saca mensajes UNO A UNO del queue global
y lanza asyncio.create_task(process_single_message(msg)) para cada uno.
�?5 Tasks de asyncio corriendo EN PARALELO con el LLM.
Cada task termina en orden variable (el LLM no es determinista en tiempo).
Si Prospecto_E termina primero:
  �?connection_manager.send_to_client("prospecto_E", respuesta)
  �?depositado en response_queues["prospecto_E"] únicamente
  �?El endpoint WS de Prospecto_E se desbloquea y envía
  �?Prospectos A, B, C, D siguen esperando en SUS propias queues
Aislamiento por Tenant: Ya garantizado por la capa de BD. crud.get_or_create_active_conversation cruza tenant_id + user_id en cada consulta. El LLM a futuro tendrá un system_prompt diferente por tenant (el TODO en 
llm.py
 ya lo anticipa). El WebSocket solo agrega el canal de transporte; no toca la lógica de aislamiento.

Compatibilidad con Múltiples Canales (Telegram, WhatsApp, Web)
Este es el argumento definitivo a favor de la Opción A.

Esta aplicación tiene canales heterogéneos con mecanismos de respuesta radicalmente distintos:

Canal	Cómo llega el mensaje	Cómo se devuelve la respuesta
Web (este Issue)	WebSocket persistente	ConnectionManager.send_to_client()
Telegram (futuro Issue)	HTTP POST webhook	POST a la Telegram Bot API
WhatsApp (futuro Issue)	HTTP POST webhook	POST a la Meta Cloud API
Con la Opción A, cuando 
process_single_message()
 llama a connection_manager.send_to_client(client_id, texto):

Si client_id existe en active_connections �?envía al socket (canal Web) �?
Si no existe (mensaje de Telegram/WhatsApp) �?pass silencioso, sin error �?
Esto significa que el canal WebSocket es completamente aditivo �?no modifica el flujo existente de ningún otro canal.

Evolución futura natural �?Response Router:

Cuando se implementen Telegram/WhatsApp, el punto de salida en 
process_single_message()
 evolucionará naturalmente hacia un router:

python
# Futuro: src/core/response_router.py
class ResponseRouter:
    async def route(self, message: IncomingMessage, response_text: str):
        if message.platform == "web":
            await connection_manager.send_to_client(message.platform_user_id, response_text)
        elif message.platform == "telegram":
            await telegram_producer.send_response(message.platform_user_id, response_text)
        elif message.platform == "whatsapp":
            await whatsapp_producer.send_response(message.platform_user_id, response_text)
Este refactor futuro es limpio porque hoy ya existe un único punto de salida controlado en 
process_single_message()
. No habrá que buscar lógica de ruteo dispersa en múltiples lugares.

El Issue #4 crea el primer canal bidireccional real del agente: un endpoint WebSocket que permite al Widget JS del sitio web de INASC conectar directamente con el brain del agente, enviando mensajes y recibiendo respuestas del LLM en tiempo real (sin polling HTTP).

User Review Required
IMPORTANT

Decisión clave de diseño �?Mecanismo de ruteo de respuesta

El reto más complejo de este Issue es: ¿cómo le regresa la respuesta del LLM al socket del cliente correcto?

El 
process_single_message
 en 
main.py
 corre como una tarea de asyncio en background, desacoplada del endpoint WebSocket. Cuando termina, tiene que enviar response_text de vuelta al cliente WebSocket que originó el mensaje.

Propuesta: el ConnectionManager actuará como el puente. Será inyectado en el proceso de mensajes vía un asyncio.Queue por-cliente (una cola de respuestas indexada por client_id), de modo que el worker puede depositar la respuesta y el endpoint WebSocket la consume para enviarla.

Alternativa más simple (para discutir contigo): el WebSocketProducer sí espera la respuesta directamente en el endpoint con un asyncio.Event o una cola privada. Este enfoque es más acoplado pero más sencillo para la primera versión.

Recomendación: usar la cola por-cliente �?te explico abajo en detalle.

WARNING

El 
process_single_message
 actualmente termina con logger.info y no devuelve nada al canal. Habrá que modificar esta función en 
main.py
 para que llame a ConnectionManager.send_to_client() al final. Esto es un cambio transversal pero quirúrgico.

Arquitectura del Flujo WebSocket
[Widget JS] ──WS Connect──�?/ws/chat/{client_id}
                �?
                �?JSON payload {"text": "...", "user_name": "..."}
                �?
        WebSocketProducer.enqueue(raw_payload)
                �?
                �?IncomingMessage (normalizado)
                �?
        queue_manager (asyncio.Queue global)  ←── ya existe
                �?
                �?
        run_agent_loop() �?asyncio.create_task(process_single_message)
                �?
                �?LLM genera response_text
                �?
        ConnectionManager.send_to_client(client_id, response_text)
                �?
                �?
[Widget JS] ◀────── JSON {"role": "agent", "content": "..."}
Proposed Changes
Componente 1 �?ConnectionManager
[NEW] connection_manager.py (file:///y:/MySource/IA/Agent-Commercial/src/core/connection_manager.py)
Clase singleton que administra el registro de clientes WebSocket activos.

python
class ConnectionManager:
    def __init__(self):
        # client_id �?WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # client_id �?asyncio.Queue (para recibir la respuesta del LLM)
        self.response_queues: dict[str, asyncio.Queue] = {}
    async def connect(self, client_id: str, websocket: WebSocket)
    def disconnect(self, client_id: str)
    async def send_to_client(self, client_id: str, message: str)
    def get_response_queue(self, client_id: str) -> asyncio.Queue
Decisión de diseño �?Cola de respuesta por cliente: Cuando se conecta un cliente, se crea una asyncio.Queue privada para él. El 
process_single_message
 deposita la respuesta en esa cola. El endpoint WebSocket está en un loop while True que: (1) espera el mensaje entrante del cliente, (2) lo encola en el brain, (3) espera la respuesta de la cola privada, (4) la envía de vuelta al socket. Esto garantiza que la respuesta siempre llega al cliente correcto aunque haya N clientes concurrentes.

Componente 2 �?WebSocketProducer
[NEW] websocket_producer.py (file:///y:/MySource/IA/Agent-Commercial/src/core/producers/websocket_producer.py)
Hereda de 
BaseProducer
. Implementa 
process_payload()
 para transformar el JSON del Widget en un 
IncomingMessage
.

python
class WebSocketProducer(BaseProducer):
    async def process_payload(self, raw_payload: dict) -> IncomingMessage:
        return IncomingMessage(
            platform="web",
            platform_user_id=raw_payload["client_id"],
            tenant_id=self.tenant_id,
            content=raw_payload["text"],
            user_name=raw_payload.get("user_name"),
        )
Nota: Como en los otros productores, 
enqueue()
 de 
BaseProducer
 se encarga de llamar a 
process_payload
 y luego a queue_manager.enqueue_message. No se re-implementa esa lógica.

Componente 3 �?Router WebSocket
[NEW] websocket.py (file:///y:/MySource/IA/Agent-Commercial/src/api/routers/websocket.py)
Endpoint FastAPI con el protocolo WebSocket completo.

python
@router.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await connection_manager.connect(client_id, websocket)
    producer = WebSocketProducer(tenant_id="inasc_web")
    response_queue = connection_manager.get_response_queue(client_id)
    try:
        while True:
            data = await websocket.receive_json()
            data["client_id"] = client_id
            await producer.enqueue(data)
            # Espera la respuesta del LLM (bloqueante asíncrono)
            response_text = await response_queue.get()
            await websocket.send_json({"role": "agent", "content": response_text})
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
Componente 4 �?Modificación de main.py
[MODIFY] main.py (file:///y:/MySource/IA/Agent-Commercial/src/main.py)
Cambio 1: Al final de 
process_single_message
, después de generar response_text, en lugar del logger.info del TODO actual, llamar a:

python
await connection_manager.send_to_client(
    message.platform_user_id, response_text
)
Cambio 2: Registrar el nuevo router:

python
from src.api.routers import websocket
app.include_router(websocket.router)
NOTE

send_to_client será tolerante a fallos: si el client_id no existe en el ConnectionManager (porque el mensaje vino por HTTP/simulate), simplemente hace pass. Esto garantiza que el simulador existente en /simulate/message siga funcionando sin cambios.

Verification Plan
Automated Tests
Test unitario �?WebSocketProducer:

bash
# Desde la raíz del proyecto con el venv activo
cd y:\MySource\IA\Agent-Commercial
pytest tests/unit/test_websocket_producer.py -v
Cubre: que 
process_payload
 genera correctamente un 
IncomingMessage
 con platform="web".

Test funcional �?Endpoint WebSocket:

bash
pytest tests/functional/test_websocket_endpoint.py -v
Usa TestClient de fastapi con soporte WebSocket (with client.websocket_connect(...)) para simular una conversación completa (mocking del LLM para no consumir API real).

Test de no-regresión �?Simulador existente:

bash
pytest tests/ -v -k "not websocket"
Verifica que ningún cambio rompió el router /simulate/message ni la lógica de BD.

Manual Verification
Arrancar el servidor:
bash
uvicorn src.main:app --reload
Abrir la consola del navegador (F12) y ejecutar:
javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat/test_user_01");
ws.onmessage = (e) => console.log("Agent:", JSON.parse(e.data));
ws.send(JSON.stringify({text: "¿Qué tipos de balanzas analíticas ofrece INASC?", user_name: "Tester"}));
Verificar que la respuesta del LLM aparece en la consola bajo Agent:.
Verificar en los logs del servidor que se muestra el flujo completo: enqueue �?LLM �?send_to_client.


El test test_websocket_connect_and_receive_response colgó �?es un deadlock. Puedes terminar el proceso con Ctrl+C.

El diagnóstico: en main.py, async_session_factory se importa con from src.database.connection import  async_session_factory (copia local del nombre). El test la parchea en src.database.connection.async_session_factory, pero esa ya no es la referencia que usa main.py. Resultado: process_single_message() intenta conectarse a MySQL real �?timeout �?send_to_client() nunca se llama �?response_queue.get() espera para siempre.

main.py  hace from src.database.connection import async_session_factory �?eso crea una copia local del nombre en el namespace de main. Cuando el test parcheaba src.database.connection.async_session_factory, cambiaba el original, pero main.py  seguía usando su copia local sin parchear. El resultado: process_single_message() intentaba conectar a MySQL real, que no estaba disponible �?timeout �?send_to_client() nunca se llamaba �?response_queue.get() esperaba eternamente.

La regla de oro: siempre parchear donde se usa, no donde se define. from X import Y �?parchear module_que_importa.Y. import X; X.Y �?parchear X.Y.