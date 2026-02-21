# Análisis de Estrategia Multi-Tenant (SaaS)
**Proyecto:** Agente Conversacional Multicanal
**Propósito:** Definir la arquitectura de base de datos y despliegue para evolucionar el Agente a un modelo SaaS (múltiples clientes/marcas).
**Fecha:** Febrero 2026

---

## 1. Contexto Comercial
El agente actual está diseñado para INASC, pero su arquitectura agnóstica a los canales (Telegram, WhatsApp, Web) permite visualizarlo como un producto B2B revendible. 
Para ofrecerlo a otros clientes, la infraestructura debe ser capaz de separar los datos, el comportamiento y los flujos comerciales de cada organización (Tenant) sin mezclar la información. 

En este análisis se comparan tres enfoques principales, incorporando mecanismos de mitigación como el **Soft Delete**.

---

## 2. Modelo A: Shared Database (Base de Datos Compartida)
Una sola instalación del código y **una sola base de datos física** procesando a todos los clientes. Todas las tablas (`leads`, `chats`, `settings`) tienen una columna obligatoria `tenant_id`.

### Ventajas (Pros):
- **Despliegue Rápido:** Dar de alta a un cliente nuevo (Onboarding) toma milisegundos (un registro en la tabla `Tenants`).
- **Eficiencia de Costos:** Se optimiza al máximo la infraestructura, consumiendo una sola piscina de conexiones a la BD.
- **Mantenimiento Simple:** Las migraciones o alteraciones de esquemas de BD se ejecutan 1 sola vez en 1 solo servidor.

### Desventajas (Cons):
- Todo el código de consultas en el Backend (FastAPI/SQLAlchemy) *debe* llevar inyectado un filtro estricto por `tenant_id`. Un ligero descuido puede causar graves fugas de datos.
- Restaurar la información completa de un solo cliente en caso de desastre es quirúrgicamente complicado sin afectar a los demás.

### Riesgos:
- **Pérdida accidental masiva por parte de un usuario Admin del cliente.**
  - **Estrategia de Mitigación (Soft Delete):** Ningún registro (`conversation`, `lead`) se borra físicamente nunca (no usar `DELETE FROM`). En su lugar, se usa una columna booleana `is_deleted = TRUE` o fecha de borrado `deleted_at = TIMESTAMP`. Esto permite la recuperación instantánea de datos ("Ouch, borré mi base de datos de leads") sin costos adicionales ni operaciones de restauración desde backups binarios.

### Oportunidades:
- Perfecta para modelos comerciales masivos y agresivos ("Self-Service B2B") donde los clientes pagan suscripciones de bajo costo con tarjeta de crédito para usar el Agente de inmediato sin fricción.

---

## 3. Modelo B: Database-per-Tenant (Una Base de Datos por Inquilino)
Un solo contenedor o clúster ejecuta el código de Python, pero el motor ORM cambia la cadena de conexión de la BD localmente dependiendo de quién envié el mensaje, guardando los datos en `db_cliente1`, `db_cliente2`, etc.

### Ventajas (Pros):
- **Seguridad y Privacidad Estricta:** Imposibilidad física y lógica de que los datos de la Empresa A aparezcan en las respuestas o reportes de la Empresa B, incluso por errores de programación.
- **Portabilidad de Datos Pura:** Es fácil extraer el dump SQL completo de un cliente si este cancela su servicio o exige llevarse su data.

### Desventajas (Cons):
- **El infierno de Migraciones automatizadas:** Añadir una nueva funcionalidad o columna implica tener que automatizar scripts que corran en 10, 50 o 1,000 bases de datos de forma transaccional usando herramientas muy especializadas.
- Altísimo consumo de conexiones y RAM en el servidor central de Base de Datos (MySQL/PostgreSQL).

### Riesgos:
- "Configurability Drift": Qué algunas de las bases de datos de los inquilinos fallen silenciomente al ser migradas a nuevas versiones, rompiendo la experiencia de clientes corporativos selectivos.

### Oportunidades:
- Se alinea excelentemente bien con corporaciones pesadas (Bancos, Bufetes Médicos, Seguros) que, por leyes de protección de datos internacionales, prohíben compartir infraestructura de base de datos con terceros.

---

## 4. Modelo C: Despliegue Multi-Instancia / On-Premise (Single-Tenant replicado)
Toda la lógica base asume que el sistema trabaja para "Un único cliente" (Single-Tenant). El aislamiento se maneja a nivel de infraestructura (Docker).

### Ventajas (Pros):
- **Máxima Flexibilidad Temprana:** Se programa de inmediato como si todo fuera solo para INASC. 
- Puedes venderle el software a un cliente que tiene un VPS propio por un costo de "Instalación y Configuración" y entregárselo encapsulado en un `docker-compose`. De allí, se auto-gestiona.
- Si 5 clientes no tienen servidor propio, puedes correr 5 copias diferentes (`docker-compose` en carpetas con distintos puertos) en tu propio servidor Linux, con distintos archivos `.env`.

### Desventajas (Cons):
- Extremadamente ineficiente a largo plazo: 100 clientes = 100 contenedores y 100 intérpretes de Python gastando gigabytes de memoria en tu servidor.

### Riesgos:
- No se puede operar como un "SaaS" barato. Requiere tu tiempo manual para "desplegar" el producto, lo que asfixia el crecimiento empresarial para volumen. Escalar implicaría el surgimiento de soluciones como *Kubernetes* u orchestradores muy avanzados.

### Oportunidades:
- **Modelo de negocio temprano ideal:** Reduce la parálisis por análisis y acelera el desarrollo inmediato. Permite tener el Agente en venta la próxima semana bajo una modalidad de "Software Dedicado / Llave en mano".

---

## 5. Próximos Pasos (Veredicto y Diseño Original Sugerido)
Se propone comenzar bajo un enfoque pragmático asumiendo código **Single-Tenant** para ganar mercado local y rapidez, pero:
> **Dejando las bases técnicas preparadas para una Migración al Modelo "Shared Database" (SaaS en Nube).**

Esto se logrará obligando a que la capa ORM central (*Models*) contemple el UUID de un `tenant_id` y atributos `is_deleted` en todas las tablas sensibles desde el Día 1, aunque todos estén apuntando localmente a un valor por defecto o nulo en esta primera versión (INASC). 
