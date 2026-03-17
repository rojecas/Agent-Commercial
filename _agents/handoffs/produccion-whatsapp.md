# Guía de Paso a Producción: WhatsApp Cloud API

Sigue estos pasos una vez que tengas la línea telefónica definitiva y el crédito de Meta.

## 1. Configuración en Meta Developers
- **Configurar Número Real**: Ve a la sección "WhatsApp" -> "Configuración de la API" y añade tu número de teléfono real. Deberás verificarlo mediante SMS o llamada.
- **Obtener Token Permanente**:
  1. Ve a "Ajustes del negocio" (Business Manager).
  2. En "Usuarios" -> "Usuarios del sistema", crea uno nuevo (rol Administrador).
  3. Haz clic en "Generar nuevo token".
  4. Selecciona tu App y marca los permisos: `whatsapp_business_messaging` y `whatsapp_business_management`.
  5. **Copia este token**: Este es el que usarás en el `.env`, ya que no expira en 24h.
- **Modo en Vivo**: Cambia el interruptor de la App de "Desarrollo" a "En vivo" (Live Mode) en la barra superior del dashboard.

## 2. Configuración del Servidor (Backend)
Actualiza las siguientes variables en tu archivo `.env`:

```env
# Usa el token permanente generado anteriormente
WHATSAPP_API_TOKEN=tu_token_permanente_aqui

# El ID del número de producción (cambiará respecto al de prueba)
WHATSAPP_PHONE_NUMBER_ID=tu_nuevo_phone_number_id

# Tu número personal o del equipo para recibir las fichas de handoff
WHATSAPP_SUPPORT_NUMBER=573006117436
```

## 3. Webhooks y URLs
- Si mantienes **ngrok**, asegúrate de que el dominio sea estático (ngrok ofrece dominios gratuitos estáticos ahora).
- Si migras a un servidor propio (VPS, Cloud), recuerda actualizar la **Callback URL** en Meta: `https://tu-dominio.com/webhook/whatsapp`.

## 4. Gestión de Créditos y Pagos
- Añade un método de pago en el **Business Manager** de Meta. 
- Recuerda que las primeras 1,000 conversaciones iniciadas por el usuario al mes suelen ser gratuitas (Service Conversations), pero las iniciadas por el bot (Marketing/Utility) requieren crédito.

## 5. Reinicio de Servicio
Una vez actualizado el `.env`, aplica los cambios:
```bash
docker-compose up -d --build
```
