# Estado Actual del Proyecto: Agent-Commercial

## 🚀 Lo que se ha completado
- **Infraestructura Dockerizada**: Backend y Base de Datos (MariaDB) corriendo en contenedores (#28).
- **Gestión Visual**: phpMyAdmin operativo en puerto 8080.
- **Canales**:
  - **Telegram**: Webhook operativo y testeado (#24).
  - **Widget Web**: Handoff visual implementado (#25).
  - **Handoff Service**: Lógica de detección de transferencia y notificación funcional.
- **Alineación de Estándares**: Refactorización completa de la carpeta `_agents/` y codificación de la **Constitución del Agente**.

## ⏳ Lo que falta por implementar
- [x] **Issue #29**: Integración de notificador para WhatsApp. (#29)
- [x] **Issue #30**: Dashboard de Asesor — Interfaz en tiempo real (WebSockets). (#30)
- [ ] **Issue #11**: Pool de API Keys — Optimización de Rate Limits para el LLM.
- [ ] **Issue #6**: Extracción Dinámica de Entidades (Lead Capture).
- [ ] **Issue #7**: Recomendaciones de Productos (Catálogo RAG).
- [ ] **Issue #8**: Integración CRM (Email de Handoff Comercial).

Especificaciones Gráficas para INASC
Si deseas personalizar los iconos y logos, utiliza estas especificaciones:

Objeto	Ruta Sugerida	Formato	Tamaño Recomendado
Logo Principal	src/static/assets/logo-inasc.svg	SVG (o PNG)	180px x 45px
Icono de App	src/static/assets/icon-inasc.svg	SVG	48px x 48px
Avatar Asesor	src/static/assets/avatar.png	PNG/WebP	128px x 128px (Círculo)


---
*Última actualización: 2026-03-19 por Antigravity*
