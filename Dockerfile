FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc en disco y forzar flush de stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias (por si acaso pymysql necesita algo)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Usaremos un servidor ASGI (Uvicorn/FastAPI) para manejar Webhooks/Websockets
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
