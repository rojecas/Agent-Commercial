# Guía de Inicio de Proyecto Agéntico Avanzado
## (Windows 10 + Git Bash + Docker)

Esta guía establece el procedimiento correcto para maximizar el uso de mis capacidades agénticas (KIs, Spec-Driven, MCP y A2A) en tu entorno específico.

---

## 1. La Constitución del Agente (Reglas de Oro)

Para evitar el desorden y el olvido de detalles, todo proyecto debe tener un archivo `_agents/constitution.md`. Este documento contiene las **normas no negociables** que yo (y cualquier otro agente) debemos seguir.

*   **Controlling the Mess**: El agente tiene prohibido crear archivos fuera de la estructura pactada.
*   **Persistent Memory**: El agente debe consultar este archivo en cada nuevo prompt de una sesión.

---

## 2. Estructura de Proyecto Estandarizada

En este workflow, **GitHub Issues es la fuente de verdad técnica y administrativa**. Nada se inicia sin un Issue.

*   **Trazabilidad**: Cada rama o worktree debe llevar el número del Issue (ej: `feature/#45-api-auth`).
*   **Definición de Terminado (DoD)**: El Issue de GitHub define *qué* hay que hacer. Mi archivo `task.md` es la versión operativa y desglosada de ese Issue para mi ejecución interna.

Para mantener el orden quirúrgico, utilizaremos la siguiente estructura:

*   **`_agents/`**: El cerebro del proyecto.
    *   `constitution.md`: Las reglas de oro.
    *   `tasks/`: Historial de `task.md` (nombrados como `task-issue-45.md`).
    *   `plans/`: Historial de `implementation_plan.md`.
    *   `walkthroughs/`: Historial de resultados y pruebas.
    *   `workflows/`: Pasos repetibles (scripts `.md`).
*   **`docs/`**: Documentación técnica generada (Arquitectura, API, Manuales).
*   **`tests/`**: Organizado por `unit/`, `functional/`, `integration/`.
*   **`logs/`**: Salidas de error, logs de Docker y depuración (añadir a `.gitignore`).

---

## 3. Fase de Diseño: Spec-Driven Development

Este es el corazón del flujo. Antes de cualquier `EXECUTION`, debemos pasar por `PLANNING`.

*   **Paso 1: implementation_plan.md**: Redactar el plan incluyendo estructura de archivos, impacto y **Plan de Verificación**.
*   **Paso 2: Aprobación**: No iniciar ejecución hasta que el plan esté aprobado por el humano.

---

## 4. Fase de Ejecución y Monitoreo (Task Management)

Mantén siempre abierto el archivo `task.md`. Mis tareas en `task.md` deben ser un reflejo granular del progreso del Issue.

---

## 5. Fase de Verificación y Documentación (Pruebas)

*   **Testing Automatizado**: Ejecución de tests dentro de contenedores Docker.
*   **Walkthrough de Verificación**: Generación de evidencias de pruebas.
*   **Actualización de Documentación**: Actualizar `README.md`, esquemas de API o manuales.
