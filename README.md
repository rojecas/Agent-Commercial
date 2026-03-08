# Agente Comercial IA Multi-Canal (FastAPI + DeepSeek)

Agente Conversacional **Multi-Tenant** para ventas técnicas y asesoramiento de productos B2B.
Opera en tiempo real a través de múltiples canales usando una arquitectura asíncrona pura en Python.

---

## 📡 Canales Implementados

| Canal | Endpoint | Estado |
|---|---|---|
| **Widget Web** (JS/WebSocket) | `GET /ws/chat/{client_id}` | ✅ Producción |
| **Telegram** | `POST /webhook/telegram` | ✅ Producción |
| **WhatsApp** (Meta Cloud API) | `POST /webhook/whatsapp` | ✅ Implementado · ⏳ End-to-end pendiente (credenciales Meta) |

---

## 🏗️ Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Framework | `FastAPI` + `uvicorn` (ASGI asíncrono) |
| LLM | DeepSeek Chat vía OpenAI SDK (`AsyncOpenAI`) |
| Base de datos | MySQL + `SQLAlchemy` async (ORM) + `aiomysql` |
| Migraciones | `Alembic` |
| HTTP externo | `httpx.AsyncClient` (Telegram, WhatsApp responders) |
| Concurrencia | `asyncio` nativo — sin Celery ni workers externos |
| Widget frontend | Vanilla JS + WebSocket API |

---

## 🧠 Arquitectura: Patrón Producer-Consumer

Todos los canales comparten el mismo núcleo. Cada canal tiene su propio **Producer** (normaliza el mensaje entrante) y **Responder** (envía la respuesta al canal). El **Agent Loop** es canal-agnóstico.

```
Canal       Producer              Queue          Agent Loop          Responder
─────       ────────              ─────          ──────────          ─────────
Widget  ──► WebSocketProducer ──►        ──────► process_single ──► connection_manager
Telegram──► TelegramProducer  ──► asyncio ────► message()      ──► TelegramResponder
WhatsApp──► WhatsAppProducer  ──► Queue   ────►   + LLM         ──► WhatsAppResponder
                                                  + MySQL
```

**Añadir un canal nuevo** = crear un `XProducer` y un `XResponder` + 1 `elif` en `main.py`.

---

## 🗄️ Esquema de Base de Datos (Multi-Tenant)

Cada tabla crítica hereda tres Mixins:
1. **`TenantMixin`** — aísla datos por `tenant_id`
2. **`SoftDeleteMixin`** — borrado lógico (`is_deleted`, `deleted_at`)
3. **`AuditableMixin`** — auditoría automática (`created_at`, `updated_at`)

```mermaid
erDiagram
    companies ||--o{ company_divisions : "has"
    company_divisions ||--o{ users : "employs"
    users ||--o{ conversations : "initiates"
    conversations ||--o{ messages : "contains"
    users ||--o{ leads_opportunities : "creates"

    users {
        BigInteger id PK
        String platform "websocket, telegram, whatsapp"
        String platform_user_id
        String tenant_id
    }
    conversations {
        BigInteger id PK
        String status "active, closed, handed_off"
        String tenant_id
    }
    messages {
        BigInteger id PK
        String role "user, assistant"
        Text content
        String tenant_id
    }
```

---

## 🚀 Arranque Local

### 1. Configurar variables de entorno
```bash
cp .env.example .env
# Edita .env con tus credenciales
```

Variables mínimas para desarrollo:
```env
DEEPSEEK_API_KEY=...
DB_URL=mysql+aiomysql://user:pass@127.0.0.1/comm_agent
TENANT_ID=inasc_001
```

### 2. Instalar dependencias y levantar el servidor
```bash
python -m venv venv
source venv/Scripts/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --host 127.0.0.1 --port 8000
```

### 3. Abrir el Widget de Chat
```
http://127.0.0.1:8000/static/widget.html
```

---

## 🔧 Configuración de Canales

### Telegram
```env
TELEGRAM_BOT_TOKEN=...
```
Registrar el webhook (una sola vez o cuando cambie la URL):
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<ngrok>.ngrok-free.app/webhook/telegram"
```

### WhatsApp (Meta Cloud API)
```env
WHATSAPP_API_TOKEN=...          # Token de la App en developers.facebook.com
WHATSAPP_PHONE_NUMBER_ID=...    # ID del número (no el número en sí)
WHATSAPP_VERIFY_TOKEN=inasc_whatsapp_verify_token  # Definido por ti
```
Configuración del webhook en Meta Developer Dashboard:
- URL: `https://<ngrok>.ngrok-free.app/webhook/whatsapp`
- Verify Token: valor de `WHATSAPP_VERIFY_TOKEN`

---

## 🧪 Tests

La suite de tests cubre los tres canales sin necesidad de credenciales reales.

```bash
# Todos los tests
./venv/Scripts/python -m pytest tests/ -v

# Por canal
./venv/Scripts/python -m pytest tests/unit/test_whatsapp_producer.py tests/functional/test_whatsapp_webhook.py -v
./venv/Scripts/python -m pytest tests/unit/test_websocket_producer.py tests/functional/test_websocket_endpoint.py -v
./venv/Scripts/python -m pytest tests/unit/test_telegram_producer.py tests/functional/test_telegram_webhook.py -v
```

**Estado actual:**

| Suite | Tests | Estado |
|---|---|---|
| Widget Web (WebSocket) | 8 | ✅ 8/8 |
| Telegram | 8 | ✅ 8/8 |
| WhatsApp | 14 | ✅ 14/14 |
| Integración DB (multi-tenant) | 4+ | ✅ Todos pasan |

---

## 🌐 Infraestructura

### Desarrollo (local + ngrok)
```
[Canal externo] → https://<id>.ngrok-free.app/webhook/... → uvicorn local (127.0.0.1:8000) → MySQL local
```

### Producción (VPS Hostinger — pendiente de aprovisionamiento)
```
[Canal externo] → https://inasc.com.co/webhook/... → Nginx (SSL) → Docker: agent-commercial → MySQL
```

| Capa | Tecnología |
|---|---|
| Proxy inverso | Nginx + Let's Encrypt |
| Runtime | Docker + docker-compose |
| VPS | Hostinger KVM (Ubuntu 22.04) |

---

## ⚙️ Git Flow

Ningún cambio se aplica directamente a `main`.

```
Issue → branch feature/issue-N-descripcion → PR → merge → cierra issue automáticamente
```




---

## 🏗️ Stack Tecnológico y Arquitectura

El sistema está construido bajo un patrón **Modular (Layered MVC)** que separa claramente el dominio del Chat, la lógica del Agente LLM, y el almacenamiento en Base de Datos.

*   **Motor (Framework):** `FastAPI` + `uvicorn` (Para máxima velocidad asíncrona y webhooks en tiempo real).
*   **Inteligencia Artificial:** OpenAI Proxy SDK consumiendo la API de **DeepSeek Chat**.
*   **Base de Datos Relacional:** `MySQL` operado mediante `SQLAlchemy` (ORM) en modo asíncrono puro (`aiomysql`). Las migraciones son manejadas por **Alembic**.
*   **Memoria de Larga Duración (Vector DB):** `ChromaDB` (Local) impulsado por `sentence-transformers`. Aquí se indexa el catálogo de productos para búsqueda semántica (RAG).
*   **Concurrencia:** Python `asyncio` nativo (sin Celery o Celery workers) respaldado por WebSockets.
*   **Limpieza de Datos:** `BeautifulSoup4` para normalizar las ricas descripciones HTML heredadas del catálogo corporativo original.

---

## 🗄️ Esquema de Base de Datos (Multi-Tenant)

El sistema fue diseñado desde el primer día para ser **SaaS Ready**. Cada tabla crítica en la base de datos (Ej: `users`, `conversations`, `leads_opportunities`) está forzada a heredar de tres Mixins de SQLAlchemy:
1.  **`TenantMixin`:** Aísla la información inyectando un `tenant_id` duro a cada registro.
2.  **`SoftDeleteMixin`:** Evita la eliminación física de registros agregando `is_deleted` y `deleted_at`.
3.  **`AuditableMixin`:** Rastrea silenciosamente `created_at` y `updated_at`.

```mermaid
erDiagram
    companies ||--o{ company_divisions : "has"
    company_divisions ||--o{ users : "employs"
    users ||--o{ conversations : "initiates"
    users ||--o{ leads_opportunities : "creates"
    conversations ||--o{ messages : "contains"
    leads_opportunities ||--o{ opportunity_product_recommendations : "receives"

    companies {
        BigInteger id PK
        String name
        String fiscal_id "NIT/RUT"
        String crm_company_id "External CRM Link"
        String tenant_id
        Boolean is_deleted
    }

    company_divisions {
        BigInteger id PK
        BigInteger company_id FK
        String name "Lab Aguas, Compras, etc"
        String crm_division_id "External CRM Link"
        String tenant_id
        Boolean is_deleted
    }

    users {
        BigInteger id PK
        BigInteger division_id FK
        String full_name
        String email
        String phone_number
        String crm_contact_id "External CRM Link"
        String platform "telegram, whatsapp"
        String platform_user_id
        Text problem_statement
        String tenant_id
        Boolean is_deleted
        DateTime created_at
    }

    conversations {
        BigInteger id PK
        BigInteger user_id FK
        String status "active, closed, handed_off"
        String intent_category "sales, support"
        String tenant_id
        Boolean is_deleted
        DateTime deleted_at
        DateTime created_at
        DateTime updated_at
    }

    messages {
        BigInteger id PK
        BigInteger conversation_id FK
        String role "user, assistant, system"
        Text content "Literal transcript"
        String tenant_id
        DateTime created_at
        DateTime updated_at
    }

    leads_opportunities {
        BigInteger id PK
        BigInteger user_id FK
        String status "qualified, needs_expert, closed"
        Text problem_statement
        String tenant_id
        Boolean is_deleted
        DateTime deleted_at
        DateTime created_at
        DateTime updated_at
    }

    opportunity_product_recommendations {
        BigInteger id PK
        BigInteger opportunity_id FK
        String product_sku
        String product_name
        Text justification "Bot reasoning"
        String tenant_id
        DateTime created_at
        DateTime updated_at
    }
```

---

## 🔌 Integración Futura con CRM

El agente está diseñado desde la base de datos para funcionar de manera simbiótica con cualquier CRM moderno (Especialmente para integraciones SaaS B2B). Las reglas arquitectónicas implementadas son:

1. **Jerarquía B2B estricta (Estilo LDAP):** En la base de datos, un Agente/Prospecto (`User`) pertenece inevitablemente a un Laboratorio/Área (`CompanyDivision`) que a su vez consolida dentro de un Cliente Principal (`Company`).
2. **Sincronización Bidireccional de IDs:** Todas las entidades core contemplan un campo `crm_*_id` (Ej: `crm_contact_id`, `crm_company_id`). Si el bot es invocado *desde* la UI de un CRM existente, el CRM puede enviar su ID único para inyectar contexto histórico al Agente de forma transparente.
3. **Inyección Dinámica de Contexto:** A través del Pydantic Model `IncomingMessage.metadata`, las integraciones externas (CRMs o ERPs) pueden pasar variables enriquecidas al vuelo (Ej. "Es un cliente VIP", "Tiene Ticket Fallando"), que el agente inyecta en su **SYSTEM PROMPT** para brindar soporte personalizado.
4. **Respeto Multi-Tenant:** Ninguna integración dependerá de variables o IDs "quemados" (Hardcoded). Todo el aislamiento se rige por el paso obligatorio del token/llave `tenant_id` en cada conexión o consulta a base de datos.
 
---

## 🧠 El Cerebro Asíncrono (Async Brain)

A diferencia de los orquestadores lang-chain/auto-gpt síncronos tradicionales, este agente no bloquea el hilo principal del servidor de API mientras "piensa" o llama a ChatGPT.

Cada webhook entrante empuja el mensaje a una cola de eventos asíncrona no bloqueante. El controlador de FastAPI se desliga inmediatamente y devuelve un `200 OK` a Telegram/WhatsApp, mientras la "Máquina de Estados" del LLM se ejecuta en tareas en segundo plano (`asyncio.create_task()`).

---

## ⚙️ Flujo de Trabajo y Ramas (Git Flow)

Este proyecto se maneja estrictamente usando **Issues**. Ninguna funcionalidad (feature) nueva ni corrección de bug se aplica directamente a la rama `main`.

1. Se reporta un requerimiento creando un **Issue**.
2. Se genera una rama derivada (`feature/ID-nombre`).
3. Se consolida a través de un Commit/Merge.

---

## 🚀 Despliegue Local (Docker)

1. Renombra `.env.example` a `.env` y añade tus credenciales (API keys, Config MySQL).
2. Construye y levanta el contenedor:
   ```bash
   docker-compose up -d --build
   ```
3. Ejecuta las migraciones de Base de datos:
   ```bash
   docker exec -it inasc_agent_backend alembic upgrade head
   ```

---

## 🧪 Estrategia de Calidad y Pruebas (Test-Driven)

Para asegurar la fiabilidad del agente autónomo, el proyecto requiere validación estricta utilizando el framework `pytest`. La estructura de pruebas está dividida en 3 carpetas dentro de `/tests`:

1.  **Unit Tests (`tests/unit/`):** Validan módulos aislados y lógica pura de negocio (por ejemplo, el formateo de prompts o la capa de integración del LLM) mockeando las dependencias externas.
2.  **Integration Tests (`tests/integration/`):** Comprueban la interacción real entre SQLAlchemy + MariaDB + Asyncio. Verifican que el flujo completo de persistencia funciona correctamente (crear usuario, abrir conversación, guardar mensajes, recuperar historial).
3.  **Functional Tests (`tests/functional/`):** Simulan el comportamiento end-to-end inyectando Webhooks completos contra FastAPI.

### Prerequisito: Base de datos de pruebas

Los tests de integración corren contra una base de datos MariaDB aislada (`comm_agent_test`). Para crearla la primera vez:
```bash
python create_test_db.py
```

### Correr los tests de integración

```bash
venv/Scripts/python.exe -m pytest tests/integration/ -v
```

**Resultado actual (Issue #3):**
```
tests/integration/test_crud.py::test_create_and_link_b2b_hierarchy  PASSED
tests/integration/test_crud.py::test_crud_chat_flow                  PASSED
2 passed, 0 warnings
```

