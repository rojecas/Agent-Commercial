# Especificación de Requisitos de Software (ERS)
**Proyecto:** Agente Conversacional Multicanal para Atención al Cliente y Captación de Leads
**Cliente:** Instruments & Applied Science INASC S.A.S.
**Versión:** 1.0
**Fecha:** febrero 2026

---

## 1. Introducción

### 1.1 Propósito
El propósito de este documento es definir las especificaciones de los requisitos de software (ERS) para el desarrollo de un Agente Conversacional Multicanal basado en Inteligencia Artificial (LLM). Este sistema actuará como la primera línea de interacción digital de la empresa, operando como un **Asesor Técnico/Comercial Virtual**.

### 1.2 Alcance
El sistema interactuará con usuarios a través de múltiples canales (Website Widget, WhatsApp, Telegram, Signal) para:
1.  Responder consultas técnicas exclusivamente basadas en la información pública del sitio web (`www.inasc.com.co`).
2.  Cualificar oportunidades de negocio (Leads) de forma conversacional.
3.  Evitar estratégicamente la entrega de información de precios.
4.  Consolidar la información del contacto y enviarla a los departamentos correspondientes (`ventas@inasc.com.co`, `webmail@inasc.com.co`).

El agente **no** realizará transacciones financieras, **no** entregará listas de precios, y **no** participará en conversaciones ajenas a los productos y servicios de INASC S.A.S.

---

## 2. Descripción General

### 2.1 Perspectiva del Producto
El agente operará como un **microservicio independiente** (aislado en un contenedor Docker) integrado en la arquitectura de sistemas existentes del sitio web corporativo de INASC (desarrollado en PHP Vanilla), adicionalmente no modifica, interrumpe ni interfiere con las funcionalidades del mismo. El agente será agnóstico al canal y estará en constante ejecución en segundo plano (Daemon 24/7), esperando pasivamente a recibir notificaciones en tiempo real (Push/Webhooks o Websockets) desde los canales de mensajería para procesarlos de inmediato frente al LLM y despachar la respuesta.

### 2.2 Funciones del Producto
*   **Recepción Multicanal:** Leer y enviar mensajes hacia Telegram, WhatsApp, Signal y el Widget Web.
*   **Triaje Conversacional Inteligente:** Capacidad de entender la intención del usuario (Ventas, Soporte Técnico, Peticiones de información general).
*   **Base de Conocimiento Estricta (RAG):** El sistema utilizará únicamente datos pre-aprobados (sitio web corporativo - primera etapa-, **documentación técnica, portafolio de productos de INASC** en segunda etapa) para generar respuestas.
*   **Extracción de Entidades Opcional:** Identificar y extraer durante la charla datos como Nombre, Correo y Descripción del Problema, de manera poco intrusiva.
*   **Handoff/Escalamiento (Fase 1):** Creación de un "Paquete de Lead" en caso de interés comercial y despacho automático de un correo a los asesores humanos.

### 2.3 Perfil de Usuarios
*   **Cliente Final:** Usuario que accede a la web o canales de mensajería buscando instrumentos de laboratorio o soporte técnico. Espera respuestas rápidas y certeras.
*   **Asesor Comercial (Usuario Interno):** Recibe por correo el resumen de la conversación y de los datos de contacto para continuar el cierre de la venta de forma manual.

### 2.4 Restricciones y Limitaciones
*   **Naturaleza del Contenido:** El bot no procesará ni generará respuestas sobre archivos multimedia (audio o imágenes) en la fase inicial. Solo consumirá texto.
*   **Restricción Comercial:** Configurado bajo *System Prompts* estrictos para jamás revelar información de costos (Precios).
*   **Limitaciones de Token:** Los mensajes de respuesta enviados al cliente tendrán un límite auto-impuesto de extensión (máximo 2 párrafos cortos equivalentes).

---

## 3. Requisitos Específicos

### 3.1 Requisitos Funcionales Integrales

**RF01 - Ingreso Omnicanal y Widget Dinámico:**
El viaje del usuario inicia en el sitio web a través de un widget inicialmente oculto (como una pestaña lateral o inferior flotante). Al desplegar la vista, el widget presenta una **pantalla de selección** que le permite al visitante elegir cómo continuar la charla:
1.  **Chat Local:** Chatear directamente en la interfaz del widget en el sitio web.
2.  **Redirección a Mensajería:** Navegar hacia WhatsApp, Telegram o Signal a través de *deep-links* (ej. `wa.me/...`) para que el usuario pueda conservar el historial de la conversación en su aplicación personal.

**RF02 - Conversación de Triaje:**
El agente deberá realizar preguntas sutiles para entender el contexto de negocio (si es una compra, un reclamo, una consulta de calibración metrológica o servicio técnico). 

**RF03 - Captura de Lead Graceful:**
Si el usuario se niega a entregar información (ej. Email), el sistema no bloqueará la interacción. Mantendrá la conversación abierta sugiriendo cordialmente escalar la inquietud de precios al correo del departamento de ventas.

**RF04 - Seguridad y Prevención de Inyecciones (Prompt Injection):**
El sistema debe procesar todas las entradas del usuario a través de un módulo Detector de Amenazas. Si la interacción intenta alterar las reglas del agente (ej. exigiendo precios o cambiando el rol del agente), el bot registrará el evento y dará una respuesta neutral por defecto.

**RF05 - Notificación por Email (Delivery):**
Cuando se ha capturado el perfil o la conversación llega a un punto de inflexión comercial, el sistema desencadena un skill interno que formatea los datos extraídos (JSON) en un cuerpo de email y lo despacha a las direcciones de correo de ventas (o la lista de correos especificada).

### 3.2 Requisitos de Arquitectura Web (Widget)
El sistema integrará un Widget flotante en la página PHP de INASC. Como se definió en RF01, este Widget será una ventana desplegable que ofrece como primera pantalla botones grandes para abrir WhatsApp/Telegram, y un botón para iniciar un "Chat Local" en la misma ventana.

Para el caso del Chat Local (en la misma web), se requiere la siguiente arquitectura:

*   **Comunicación WebSockets.** El widget abrirá un túnel bidireccional mediante WebSockets directamente al servidor Python, saltándose PHP. Esto garantiza comunicación en tiempo real ("typing..."), latencia baja y percepción "premium". (Requiere configurar Nginx para tráfico `ws://` o `wss://`).

### 3.3 Requisitos de Integración Backend (Canales de Mensajería Externos)
Para garantizar la fluidez en canales externos (Telegram, WhatsApp) y evitar el uso ineficiente de recursos de servidor, queda estrictamente prohibido el uso de técnicas de *Polling* (consultas temporizadas continuas).
*   **Arquitectura Webhook (Push):** La integración con las APIs de Telegram y el futuro WhatsApp Cloud API se realizará mediante Webhooks. El servidor Nginx expondrá endpoints seguros (`https://inasc.com.co/api/webhook/telegram`) que recibirán notificaciones en tiempo real (Push) directamente desde los servidores de Meta/Telegram en el milisegundo exacto en que el usuario envía un mensaje.

### 3.4 Requisitos de Despliegue (Infraestructura)
*   **Entorno de Ejecución:** El artefacto completo (backend Python) correrá en contenedores **Docker**, estandarizados mediante `docker-compose`.
*   **Sistema Operativo Base:** Servidor/Máquina Virtual basada en Linux (ej. Debian/Ubuntu).
*   **Proxy Inverso (Obligatorio):** Se requerirá **Nginx** o equivalente para el manejo y terminación de certificados SSL explícitamente necesarios para el registro seguro de Webhooks, además del mapeo de puertos internos hacia la web pública (80/443).
*   **Recurrencia/Caída (Fallback):** Si el LLM no responde por cuellos de botella en la red, el sistema pasará a un conjunto de respuestas estáticas disculpándose e indicando canales humanos.

### 3.5 Integración de Base de Conocimiento (Catálogo de Productos)
*   **Acceso Controlado a Datos:** El agente leerá la información técnica conectándose directamente a la base de datos MySQL (tablas `i3_productos`, `i3_categorias`, `in_columnas`), pero **exclusivamente a través de interfaces (`tools`) programadas en Python**, eliminando cualquier riesgo de modificación accidental o maliciosa (Inyección SQL).
*   **Limpieza de Datos (Sanitización):** Los campos técnicos y descriptivos de la base de datos están en formato de texto enriquecido (HTML). El sistema implementará un middleware en Python que extraiga y elimine estas etiquetas HTML antes de inyectar el contexto al LLM, reduciendo el consumo de tokens.
*   **Gestión de Descargas/Manuales:** La base de datos guarda las referencias relativas (rutas) de folletos y manuales. El agente utilizará estas rutas para referenciar documentos estáticos a los clientes si estos solicitan más información.
*   **Herramienta de Búsqueda Unificada:** Se diseñará una única `tool` multipropósito capaz de recibir parámetros variables (búsqueda por nombre, SKU, marca, categoría o palabra clave), dándole al agente autonomía para encontrar el producto exacto con un solo llamado al sistema.

---

## 4. Criterios de Aceptación (Verificación)

El software se considerará listo cuando se valide lo siguiente:
1.  **Simulación de Compra:** Un usuario prueba solicitar la cotización de un equipo; el bot explica características, captura el correo y envía exitosamente el resumen a `ventas@inasc.com.co` sin revelar nunca el precio.
2.  **Prueba de Seguridad (Fuzzing):** El bot resiste, bloquea e ignora preguntas fuera de contexto o comandos agresivos para obligarlo a romper su rol (ej. Preguntas políticas o *jailbreaks*).
3.  **Cross-platform Test:** El mismo formato de mensaje de atención es servido coherentemente tanto en WhatsApp como a través del Widget Web.
