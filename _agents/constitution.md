# Constitución del Agente (Reglas de Oro)

Este documento es de lectura **obligatoria** para cualquier agente que participe en este proyecto. El incumplimiento de estas reglas se considera un fallo crítico en la tarea.

---

## 1. Orden y Estructura de Archivos
*   **Aislamiento**: Todo archivo generado por el agente (planes, tareas, resultados) DEBE residir en la carpeta `_agents/`.
*   **Prohibición de "Clutter"**: No se permite crear archivos temporales en la raíz del proyecto. Usa `/tmp/` o la estructura definida en `_agents/`.
*   **Nomenclatura**: Los archivos de proceso deben incluir el ID del Issue de GitHub (ej: `tasks/task-issue-45.md`).

## 2. Calidad y Verificación
*   **No Vibe-Coding**: Antes de implementar cualquier lógica, debe existir un `implementation_plan.md` aprobado.
*   **Test-Driven Execution**: Todo código nuevo debe ir acompañado de sus respectivos tests en la carpeta `tests/`.
*   **Verificación en Contenedor**: Los tests deben ejecutarse dentro del contenedor Docker del proyecto, no en el host.

## 3. Documentación y Traspaso (Handoff)
*   **Auto-Documentación**: Cada vez que se modifique una funcionalidad, se debe actualizar el archivo correspondiente en `docs/`.
*   **Handoff de Proyecto (`_agents/handoff.md`)**: Este archivo DEBE mantenerse actualizado como el "Estado del Arte" del proyecto. Debe contener:
    *   Qué se ha completado.
    *   En qué se está trabajando actualmente.
    *   Qué falta por implementar (Roadmap).
*   **Handoff de Issue (`_agents/handoffs/handoff-issue-N.md`)**: Al finalizar un Issue, el agente debe generar un documento específico con los detalles técnicos de ese cambio para facilitar la auditoría y el contexto inmediato.

## 4. Control de Versiones y GitHub (Fuente de Verdad)
*   **GitHub MCP Obligatorio**: El agente DEBE utilizar las herramientas de MCP de GitHub para interactuar con el repositorio remoto. Si no están activas, debe solicitar su activación.
*   **Workflow Centrado en Issues**: Todo trabajo DEBE iniciar y terminar en un Issue de GitHub.
*   **Gestión de Ramas**: El desarrollo se realiza en ramas de feature (ej: `feat/issue-28-infra`). Al terminar, se debe sincronizar con `main`, resolver conflictos y realizar el push.
*   **Cierre Remoto**: Al finalizar un Issue, el agente DEBE:
    1.  Subir todos los cambios locales.
    2.  Utilizar `mcp_github-mcp-server_add_issue_comment` para registrar un resumen técnico, enlazando los artefactos en `_agents/walkthroughs/`.
    3.  Utilizar `mcp_github-mcp-server_issue_write` con `method: 'update'` y `state: 'closed'` para cerrar el Issue formalmente.
*   **Handoff y GitHub**: El Roadmap en `_agents/handoff.md` debe referenciar los números de Issue de GitHub para mantener la trazabilidad.

## 5. Comunicación
*   **Transparencia**: El archivo `task.md` debe estar siempre actualizado. Si el agente se encuentra bloqueado, debe notificarlo inmediatamente en el Issue de GitHub o vía `notify_user`.

## 6. Skills y Workflows (Habilidades Procedimentales)
*   **Ubicación**: Los flujos de trabajo específicos del proyecto residen en `_agents/workflows/`.
*   **Uso de Skills**: El agente debe consultar esta carpeta antes de realizar tareas complejas de despliegue, testing o mantenimiento.
*   **Automatización (Turbo)**: Se permite la ejecución automática de pasos marcados con `// turbo` siempre que el entorno sea estable.
