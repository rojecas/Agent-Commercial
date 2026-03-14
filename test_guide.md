# Guía de Prueba Manual: Sistema de Handoff Omnicanal

Esta guía detalla los pasos para validar que el sistema de transferencia a asesores funciona correctamente tanto para clientes en la Web como en Telegram.

## Preparación del Entorno
Antes de empezar, asegúrate de que:
1. **Servidor Local**: Ejecutar `./venv/Scripts/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload`
2. **Túnel ngrok**: Ejecutar `ngrok http 8000` y asegurar que la URL coincida con el webhook registrado en Telegram.
3. **Base de Datos**: MySQL (XAMPP) debe estar encendido.
4. **Configuración .env**:
   - `TELEGRAM_ADVISOR_GROUP_ID`: Debe ser tu ID de Telegram o el de un grupo de prueba.
   - `WEB_CHANNEL_TENANT_ID`: Debe ser `inasc_001`.

---

## Prueba 1: Cliente desde Telegram
*Simula a un cliente que usa el bot oficial.*

1. **Cliente (Celular 1)**: Abre el chat con [@Test3759_AM_bot](https://t.me/Test3759_AM_bot).
2. **Acción**: Escribe: *"Hola, tengo interés en una balanza industrial y deseo hablar con un vendedor"*.
3. **Verificación Cliente**: El bot debe responder: *"✅ Te estamos conectando con Carlos Pérez..."*.
4. **Verificación Asesor (Celular 2 / PC)**: En el chat/grupo configurado como `TELEGRAM_ADVISOR_GROUP_ID`, debe llegar un mensaje detallado con el resumen del caso generado por la IA.

---

## Prueba 2: Cliente desde el Widget Web
*Simula a un cliente navegando en el sitio de INASC.*

1. **Cliente (Celular 1 o Navegador)**: Abre la URL: `https://<TU_ID_NGROK>.ngrok-free.app/static/widget.html`.
2. **Acción**: Inicia el chat y escribe: *"¿Tienen soporte técnico disponible ahora? Quisiera hablar con una persona"*.
3. **Verificación Cliente**: El widget debe mostrar el mensaje de conexión exitosa mencionando a **Carlos Pérez** 🤝.
4. **Verificación Asesor (Telegram)**: El equipo de ventas recibirá en Telegram una alerta que dice: `📱 Canal: web`, permitiéndoles saber que hay alguien esperando en el sitio web.

---

## Notas de Validación
- [ ] ¿El bot dejó de responder automáticamente después del handoff? (Debería estar en silencio).
- [ ] ¿El nombre del asesor asignado es correcto?
- [ ] ¿El resumen del caso refleja fielmente lo que pidió el cliente?
