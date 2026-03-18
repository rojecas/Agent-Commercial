# Plan de Implementación - Issue #30: Dashboard de Asesor

Desarrollar una interfaz básica (Dashboard) para que asesores humanos gestionen conversaciones transferidas (`handed_off`).

## Cambios Propuestos

### Base de Datos y CRUD
#### [MODIFY] `src/database/crud.py`
Añadir funciones para:
- `get_handed_off_conversations`: Obtener lista de chats pendientes de atención.
- `get_messages_by_conversation`: Obtener el historial completo de una conversación para el asesor.

### Capa de API
#### [NEW] `src/api/routers/dashboard.py`
Crear router con los siguientes endpoints:
- `GET /api/dashboard/conversations`: Retorna la lista de chats en estado `handed_off`.
- `GET /api/dashboard/conversations/{id}/messages`: Historial de chat.
- `POST /api/dashboard/conversations/{id}/reply`: Envía un mensaje manual (inyectando en la plataforma de origen).
- `POST /api/dashboard/conversations/{id}/close`: Devuelve el control al bot (status `active`).

### Interfaz de Usuario (Frontend)
#### [NEW] `src/static/dashboard.html`
Estructura de dos columnas: listado de chats a la izquierda, ventana de chat a la derecha.

#### [NEW] `src/static/dashboard.js`
Lógica para:
- Polling (o WebSockets) para actualizar la lista de chats.
- Cargar mensajes al seleccionar un chat.
- Enviar respuestas vía API.

### Orquestación Core
#### [MODIFY] `src/main.py`
- Registrar el nuevo router `dashboard.py`.

## Plan de Verificación

### Pruebas Automatizadas
- Crear `tests/unit/test_dashboard_api.py` para validar los endpoints de listado y respuesta manual.

### Verificación Manual
- Iniciar una conversación vía WhatsApp/Telegram.
- Forzar el handoff pidiendo un asesor.
- Abrir `http://localhost:8000/static/dashboard.html`.
- Verificar que el chat aparece en la lista.
- Responder desde el dashboard y verificar que el mensaje llega al teléfono del usuario.
- Cerrar el caso y verificar que el bot vuelve a responder.
