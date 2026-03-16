# Estándar de Documentación: Desarrollo Híbrido (Humano + IA)

Para que un proyecto sea mantenible y "agent-friendly", debe existir un equilibrio entre la documentación de ingeniería tradicional y los metadatos de contexto para la IA.

---

## 1. Capa de Negocio y Requerimientos (El "Qué")
Ubicar en: `docs/requirements/`

| Documento | Descripción | Importancia para la IA |
| :--- | :--- | :--- |
| **User Stories** | Funcionalidades desde la perspectiva del usuario. | Entender el valor de negocio y criterios de aceptación. |
| **ERS/SRS** | Especificación de Requerimientos de Software. | Evita ambigüedades en reglas lógicas. |
| **Data Dictionary** | Definición de campos y relaciones. | Crucial para evitar invención de esquemas. |

---

## 2. Capa de Arquitectura y Diseño (El "Cómo")
Ubicar en: `docs/architecture/`

| Documento | Descripción | Importancia para la IA |
| :--- | :--- | :--- |
| **Architecture Blueprint** | Diagrama de flujos y componentes. | Entender dónde encaja el código. |
| **SSD (System Design)** | Decisiones técnicas y patrones. | Asegura el uso de patrones del proyecto. |
| **API Spec** | Contratos de API (OAS/Swagger). | Generación de mocks y tests de integración. |

---

## 3. Capa Agéntica (La Coordinación IA)
Ubicar en: `_agents/`

| Documento | Descripción | Importancia para la IA |
| :--- | :--- | :--- |
| **`constitution.md`** | Reglas de oro y restricciones. | Brújula técnica del agente. |
| **`implementation_plan.md`** | Plan paso a paso. | Validación humana antes de ejecución. |
| **`task.md`** | Checklist operativo. | Seguimiento del progreso. |

---

## 4. Capa Técnica y Operativa (La Verificación)
Ubicar en: `_agents/walkthroughs/` y `tests/`

| Documento | Descripción | Importancia para la IA |
| :--- | :--- | :--- |
| **Handoff Document** | Resumen de cierre para la siguiente sesión. | Evita pérdida de contexto. |
| **Walkthroughs** | Evidencias de pruebas. | Auditoría de calidad. |
| **ADR** | Registro de decisiones arquitectónicas. | Evita "correcciones" de lógica intencional. |
