# Patrones de Arquitectura en FastAPI: Análisis Comparativo

FastAPI es un micro-framework (como Flask) no un macro-framework (como Django o Laravel). Esto significa que no impone ninguna estructura de carpetas; eres libre de organizarlo como quieras. Sin embargo, para un proyecto corporativo Multi-Tenant como el que estamos construyendo, elegir la arquitectura correcta dede el día uno es vital para no terminar con código "espagueti".

Aquí presentamos los 3 enfoques principales aplicables a nuestro Bot Comercial y sus Pros/Contras.

---

## 1. Patrón Plano / Orientado a Archivos (Micro-App)
Toda la lógica se divide en unos pocos archivos centralizados según su rol técnico (Modelos aquí, Rutas allá).

*Estructura de Carpetas:*
```text
src/
├── main.py           (Inicialización de FastAPI)
├── models.py         (Todas tus clases SQLAlchemy juntas)
├── schemas.py        (Todos tus Pydantic models juntos)
├── routes.py         (Todos los endpoints de la API juntos)
└── database.py       (Conexión)
```

*   **Pros:**
    *   Súper fácil de configurar y entender para proyectos pequeños.
    *   Curva de aprendizaje casi nula.
*   **Contras:**
    *   Escala terriblemente mal. Cuando tengas 20 tablas de base de datos y 50 endpoints, el archivo `routes.py` va a tener 3,000 líneas de código inmanejables.
    *   **Veredicto:** Descartado para INASC. Nuestro bot tiene demasiadas responsabilidades (Webhooks, LLM Agents, Base de Datos, Vector DB).

---

## 2. Patrón MVC Adaptado / Orientado por Dominio (Layered)
Se separan las responsabilidades en "Módulos" lógicos que representan las partes del negocio (Usuarios, Chats, Productos). Cada módulo contiene su propia base de datos, lógia pura, y rutas API.

*Estructura de Carpetas:*
```text
src/
├── main.py
├── core/             (Configuración global, db.py, seguridad.py)
├── api/
│   ├── users/        (Todo lo relacionado a usuarios)
│   │   ├── router.py (Endpoints web)
│   │   ├── crud.py   (Lógica directa a base de datos)
│   │   ├── models.py (SQLAlchemy para usuarios)
│   │   └── schemas.py(Pydantic para usuarios)
│   ├── chat/         (Todo lo relacionado a los Webhooks y mensajes) ...
│   └── agent/        (La lógica fuerte de IA, Skills y LLM) ...
```

*   **Pros:**
    *   Alta mantenibilidad. Si hay un problema en el chat, vas directamente a la carpeta `chat` y ahí está todo centralizado.
    *   Evita archivos gigantescos de miles de líneas.
    *   Es el estándar más usado en la industria moderna de FastAPI.
*   **Contras:**
    *   Si los módulos no se diseñan bien, pueden crearse dependencias circulares (Ej. el Módulo de Usuarios necesita el Módulo de Chat, y viceversa).
    *   Requiere disciplina estricta del programador.
    *   **Veredicto:** Esta es la **Arquitectura Recomendada** para el 90% de los proyectos serios. Es excelente para nosotros.

---

## 3. Patrón DDD (Domain-Driven Design) o Arquitectura Hexagonal
Una separación hiper-estricta del código en capas. La lógica de negocio o "Dominio" está en el centro, y cosas como la Base de Datos o la API de Telegram son simples "Adaptadores" periféricos intercambiables.

*Estructura de Carpetas:*
```text
src/
├── domain/            (Reglas de negocio puras, sin bases de datos ni web)
├── application/       (Casos de uso: registrar usuario, analizar mensaje)
├── infrastructure/    (Alembic, SQLAlchemy, clientes de HTTP)
│   └── database/      (Repositorios que implementan interfaces del dominio)
└── presentation/      (FastAPI routers, Webhooks de Telegram/WhatsApp)
```

*   **Pros:**
    *   Separación total. Puedes cambiar de MySQL a MongoDB mañana, o de FastAPI a Django, y el núcleo de la aplicación (Reglas del bot) no cambia.
    *   Testabilidad casi perfecta.
*   **Contras:**
    *   *Over-engineering* (Sobreingeniería) masiva para la mayoría de startups.
    *   Escribes 3 veces más código debido a las inmensas capas de abstracción (Interfaces, Repositorios, Servicios).
    *   **Veredicto:** Solo recomendable para bancos o sistemas multinacionales con decenas de equipos de desarrolladores. Para nosotros añadiría una barrera de desarrollo innecesariamente pesada.

---

## Recomendación Final para el Agente Comercial: **Opción 2 (Layered/Modular)**

Este es el enfoque híbrido que te sugiero implementar en `src/`. Vamos a dividir el proyeto por "Dominios":

1.  **`src/database/`**: El núcleo de datos (que ya tienes con `base.py`, `models.py`, `connection.py`).
2.  **`src/agent/`**: Todo el cerebro del Bot. Aquí vivirán las carpetas de `skills`, `tools` y la orquestación del LLM.
3.  **`src/webhooks/`**: Controladores de FastAPI que solo reciben mensajes de Telegram, WhatsApp o Web, los empaquetan, se los mandan a `src/agent/`, y devuelven la respuesta asíncrona al cliente.
4.  **`src/services/`** (CRUD): Funciones que sirven de puente entre el cerebro (agent) y la base de datos para guardar/leer oportunidades.

---

## Anexo para Desarrolladores Laravel: ¿Dónde quedó el MVC?

Si vienes de Laravel, el salto a FastAPI puede parecer desordenado al principio porque no hay carpetas `app/Http/Controllers` o `app/Models` por defecto. FastAPI no usa el patrón MVC tradicional porque **está diseñado puramente para APIs, no para renderizar vistas HTML (Blade)**. 

Sin embargo, el Patrón Modular (Opción 2) es esencialmente el equivalente uno-a-uno del MVC moderno en backend. Aquí tienes la traducción exacta de conceptos:

| Concepto en Laravel (MVC) | Equivalente en FastAPI (Modular) | Descripción Práctica en nuestro Proyecto |
| :--- | :--- | :--- |
| **Model (Eloquent)** | `models.py` (SQLAlchemy) | Las clases que mapean tus tablas SQL. Las pusimos en `src/database/models.py`. Hacen lo mismo que `artisan make:model`. |
| **View (Blade)** | *Inexistente / Respuestas JSON* | No tenemos vistas visuales. Nuestras "vistas" son literalmente las respuestas JSON que el Agente y los Webhooks escupen a Telegram o WhatsApp. |
| **Controller** | `router.py` (Controladores) | Las funciones que tienen el decorador `@app.post("/webhook")`. En nuestro caso vivirán dentro de la carpeta `src/webhooks/`. Son el punto de entrada. |
| **FormRequests / Validaciones** | `schemas.py` (Pydantic) | En Laravel usas FormRequests para validar que el input sea un String o un Email. En FastAPI usamos clases de Pydantic. Son el escudo protector de los Controladores. |
| **Service Classes / Repositories** | `services.py` o `crud.py` | En Laravel moderno evitas meter lógica gorda en el Controlador. En FastAPI hacemos lo mismo: el webhook de Telegram recibe el texto y se lo pasa ciegamente a una función de `src/services/` o `src/agent/` para que trabaje. |
| **Migrations (`2024_create_...`)** | `alembic` (Migraciones) | En Laravel corres `artisan migrate`. Aquí correremos `alembic upgrade head`. Es el mismo principio del gestor de historial de esquemas. |

En resumen: En Laravel agrupas por **Capa Técnica** (Todos los controladores juntos, todos los modelos juntos). En el Patrón Modular de FastAPI que elegimos, agrupamos por **Concepto de Negocio** (Todo lo de usuarios junto, todo lo de chat junto). Es un "MVC Distribuido" que te dará muchísima más paz mental cuando la app crezca.

¿Qué opinas de consolidar esta estructura de carpetas (Opción 2) en el proyecto real?
