# Walkthrough - Prueba End-To-End Telegram Handoff (#24)

Validación del flujo completo de transferencia a asesor vía Telegram.

## Resultados de la Prueba
- **Registro de Asesor**: Carlos Pérez creado en la tabla `advisors` (tenant inasc_001).
- **Trigger**: Mensaje enviado desde Telegram.
- **Acción LLM**: Solicitud de handoff detectada por el servicio.
- **Notificación**: Alerta recibida en el grupo de Telegram configurado.
- **Respuesta**: El bot informó al cliente sobre la transferencia exitosa.
