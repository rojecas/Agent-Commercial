# Plan: Mejora de Infraestructura y Documentación (#28)

Este plan aborda la unificación del entorno de desarrollo moviendo la base de datos a Docker y clarificando los requisitos del sistema.

## User Review Required

> [!IMPORTANT]
> **Migración de Base de Datos a Docker**
> Se añadió un servicio de MariaDB al `docker-compose.yml`. Esto permite un arranque unificado con `docker-compose up`.
> - La base de datos local (XAMPP) deja de ser el objetivo principal en desarrollo Docker.
> - Se requiere que el usuario tenga **Docker** y **Ngrok** instalados.

---

## Cambios Propuestos

### Documentación
#### [MODIFY] [README.md](file:///y:/MySource/IA/Agent-Commercial/README.md)
- Añadir sección de **Prerrequisitos** (Docker, Ngrok).
- Actualizar la guía de inicio rápido para usar `docker-compose`.

### Infraestructura (Docker)
#### [MODIFY] [docker-compose.yml](file:///y:/MySource/IA/Agent-Commercial/docker-compose.yml)
- Añadir servicio `db` con imagen `mariadb:10.11`.
- Configurar variables de entorno para la base de datos (`MYSQL_DATABASE`, `MYSQL_ROOT_PASSWORD`, etc.).
- Añadir volumen persistente `./docker/mysql_data`.
- Asegurar que `app` dependa de `db` y use la red de Docker.

#### [MODIFY] [.env.example](file:///y:/MySource/IA/Agent-Commercial/.env.example)
- Cambiar `DB_HOST=127.0.0.1` por `DB_HOST=db` para compatibilidad con Docker.

#### [MODIFY] [.env](file:///y:/MySource/IA/Agent-Commercial/.env)
- Sincronizar con los cambios de `.env.example` para que el entorno local Docker funcione de inmediato.

---

## Plan de Verificación

### Pruebas Automatizadas
1. **Levantar servicios**: Ejecutar `docker-compose up -d --build`.
2. **Migraciones**: Ejecutar `docker exec inasc_agent_backend alembic upgrade head`.
3. **Tests de integración**: Ejecutar `docker exec inasc_agent_backend pytest tests/integration/test_multi_tenant.py` (para verificar persistencia).

### Verificación Manual
1. Abrir el log de `inasc_agent_backend` y confirmar que no hay errores de conexión a la DB.
2. Acceder al dashboard de MariaDB si es necesario (vía `docker exec`).
