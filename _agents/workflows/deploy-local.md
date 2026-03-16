---
description: Procedimiento para desplegar el entorno de desarrollo local usando Docker
---

# Skill: Despliegue Local (deploy-local)

Este workflow permite levantar el entorno de desarrollo completo. Sigue estos pasos para asegurar un despliegue limpio y funcional.

## Requisitos Previos
- Docker Desktop instalado y en ejecución.
- Git Bash o terminal compatible.

## Pasos del Workflow

1. **Limpiar entorno previo (Opcional)**:
Si hay contenedores antiguos o colgados, elimínalos para evitar conflictos de puertos.
// turbo
```bash
docker-compose down -v --remove-orphans
```

2. **Levantar Contenedores**:
Inicia los servicios definidos en el archivo `docker-compose.yml`.
// turbo
```bash
docker-compose up -d
```

3. **Verificar Estado de los Servicios**:
Asegúrate de que todos los contenedores estén en estado "Up".
// turbo
```bash
docker-compose ps
```

4. **Instalación de Dependencias**:
Si el proyecto usa Node/PHP/Python, ejecuta la instalación dentro del contenedor principal.
// turbo
```bash
docker-compose exec app npm install
```

5. **Ejecutar Migraciones**:
Sincroniza la base de datos con el esquema actual.
// turbo
```bash
docker-compose exec app npm run migrate
```

---
> [!TIP]
> Si el paso 2 falla por conflicto de puertos, verifica que no tengas otros servicios ocupando el puerto 80/443 o 3306.
