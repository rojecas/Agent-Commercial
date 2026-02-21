# Configuración del Entorno de Desarrollo (Docker & Python)

Este flujo de trabajo describe los pasos estandarizados para preparar, levantar y mantener el entorno de desarrollo local del Agente Comercial Multicanal utilizando Docker.

## 1. Requisitos Previos
- **Docker Engine** y **Docker Compose** instalados en la máquina de desarrollo.
- Acceso a un editor de código (ej. VSCode).
- Credenciales iniciales para LLM (OpenAI/DeepSeek API Key) y Telegram (Bot Token) para pruebas en local.

## 2. Estructura de Directorios del Proyecto
La arquitectura del proyecto debe organizarse de la siguiente manera antes de levantar los contenedores:

```text
/Agent-Commercial
├── docker-compose.yml       # Orquestador de servicios (App, Redis, DB mock)
├── Dockerfile               # Receta de construcción de la imagen Python
├── requirements.txt         # Dependencias de Python
├── .env                     # Variables de entorno locales (NO COMITEAR)
├── .env.example             # Plantilla de variables de entorno
├── workflow.md              # Esta guía
├── ERS_Agente_Comercial.md  # Especificación de Requisitos
├── src/                     # Código fuente del Agente
│   ├── core/                # Lógica principal (LLM, prompt, queue)
│   ├── producers/           # Conectores de entrada (Webhooks, Telegram, WhatsApp)
│   ├── tools/               # Skills del agente (Búsqueda DB, Enviar Email)
│   └── database/            # Conectores y queries a MySQL
└── logs/                    # Directorio montado como volumen para logs
```

## 3. Preparación del Entorno (Paso a Paso)

### Paso 3.1: Configurar Variables de Entorno
1. Copia el archivo `.env.example` a un nuevo archivo llamado `.env`.
2. Llena los valores sensibles en el `.env` (ej. `OPENAI_API_KEY`, credenciales de base de datos MySQL de desarrollo).

### Paso 3.2: Inicialización del Repositorio Git y GitHub
Es fundamental versionar el código antes de comenzar el desarrollo intensivo.

1. Inicializa el repositorio local en la raíz del proyecto:
```bash
git init
```
2. Añade los archivos iniciales al área de preparación (stage) y crea el primer commit:
```bash
git add .
git commit -m "chore: setup inicial del entorno docker, ERS y estructura de directorios"
```
3. Crea un repositorio vacío en GitHub (sin README, ni .gitignore, ni licencia para evitar conflictos).
4. Vincula tu repositorio local con el de GitHub y sube los cambios (reemplaza `<TU_USUARIO>` y `<TU_REPO>`):
```bash
git branch -M main
git remote add origin https://github.com/rojecas/Agent-Commercial.git
git push -u origin main
```

### Paso 3.3: Instalación Local (Opcional - Para Intellisense/Autocompletado)
Si deseas trabajar con el entorno virtual localmente (fuera de Docker) para beneficiarte del autocompletado en tu IDE:
```bash
python -m venv venv
# Activar en Windows:
.\venv\Scripts\activate
# Activar en Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### Paso 3.4: Construir y Levantar Contenedores con Docker
Este es el método recomendado para garantizar que todos los desarrolladores tengan el mismo entorno.

1. Abre una terminal en la raíz del proyecto.
2. Construye la imagen y levanta los servicios en segundo plano:
```bash
docker-compose up --build -d
```
3. Para verificar que el agente está corriendo correctamente (Daemon), revisa los logs:
```bash
docker-compose logs -f app
```

### Paso 3.5: Detener el Entorno
Cuando termines de desarrollar, puedes apagar los contenedores sin perder datos (los volúmenes se mantienen):
```bash
docker-compose down
```

## 4. Notas sobre Webhooks en Desarrollo Local
Dado que el agente usará **Webhooks**, servicios como Telegram y WhatsApp necesitan una URL pública (HTTPS) para enviar los mensajes a tu máquina local.
- **Solución:** Utiliza herramientas como **Ngrok** o \`localtunnel\` para exponer el puerto interno de tu contenedor Docker (ej. 8000) a internet de forma segura durante la fase de desarrollo.
