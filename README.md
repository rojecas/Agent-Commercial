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
