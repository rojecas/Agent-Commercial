# Análisis Arquitectónico: Dashboard Omnicanal para Asesores

Este documento analiza las implicaciones y el diseño necesario para transformar el sistema de Handoff actual en una plataforma donde los asesores humanos puedan responder a los clientes de forma bidireccional, independientemente del canal (WhatsApp, Telegram, Web, etc.).

## 1. Visión General
El objetivo es que el asesor no solo sea *notificado* de un handoff, sino que pueda entrar a una interfaz centralizada para chatear con el cliente. El "cerebro" (Agent-Commercial) actuará como un hub central de ruteo.

## 2. Cambios Requeridos en el Modelo de Datos

Para soportar la sesión humana, la base de datos debe evolucionar:

### 2.1 Tabla `conversations`
- **Nuevo campo**: `assigned_advisor_id (BigInteger, FK)`.
  - Permite saber exactamente qué asesor es dueño de la conversación una vez transferida.
- **Nuevo estado**: `waiting_for_advisor` (opcional, entre el handoff y la primera respuesta humana).

### 2.2 Tabla `messages`
- **Nuevo campo**: `sender_type (String)`. Valores: `bot`, `human_advisor`.
  - Permite distinguir en el historial quién dio cada respuesta.
- **Nuevo campo**: `advisor_id (BigInteger, FK, nullable)`.
  - Si el mensaje es una respuesta humana, queda registrado quién lo envió para auditoría.

---

## 3. Ruteo de Salida Unificado (Omnichannel Router)

Actualmente, los `responders` solo son llamados por el `Agent Loop`. Para que un asesor pueda enviar mensajes, necesitamos un servicio de ruteo inverso:

1. **Input**: `conversation_id`, `text_content`.
2. **Proceso**:
   - Buscar la `Conversation` y su `User` asociado.
   - Identificar el `platform` del usuario ('telegram', 'web', 'whatsapp').
   - Recuperar el `platform_user_id`.
3. **Output**: Llamar al canal correspondiente:
   - Si es Web → `connection_manager.send_to_client()`
   - Si es Telegram → `telegram_responder.send_message()`
   - Si es WhatsApp → `whatsapp_responder.send_message()`

---

## 4. Nuevos Endpoints (Dashboard API)

Para que el Dashboard (frontend) funcione, el API de FastAPI debe exponer:

- `GET /advisors/conversations`: Lista de chats activos asignados al asesor logueado.
- `GET /conversations/{id}/history`: Historial completo (mensajes de IA + cliente) para que el asesor tenga contexto.
- `POST /conversations/{id}/reply`: Envía el texto del asesor al cliente a través del *Omnichannel Router*.
- `POST /conversations/{id}/close`: Devuelve el control al Bot o cierra el caso.

---

## 5. Complejidad y Esfuerzo

> [!IMPORTANT]
> **¿Es mucho cambio?**
> No. La arquitectura actual es muy modular. 
> - Ya tenemos los **Responders** (la parte difícil de conectarse a las APIs de Telegram/WhatsApp).
> - Ya tenemos el **Handoff Service** que detecta el momento de cambio. 
> - El esfuerzo se centraría en un **80% en crear los nuevos endpoints de API y el 20% en ajustes a los modelos**.

---

## 6. Próximos Pasos Recomendados

1. **Fase 1**: Refactorizar los modelos `Conversation` y `Message`.
2. **Fase 2**: Crear el `OutboundRoutingService` para mensajes manuales.
3. **Fase 3**: Implementar los endpoints de API básicos para lectura de chats.
4. **Fase 4**: Crear una interfaz web (frontend) simple para el asesor.
