import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 1. Cargar variables de entorno desde el archivo .env
load_dotenv()

# Extraer credenciales
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

# 2. Construir la URL de Conexión ASÍNCRONA
# Nota: Usamos 'mysql+aiomysql' en lugar de 'mysql+pymysql'
# Esto le dice a SQLAlchemy que use el driver no bloqueante que acabas de ver en requirements.txt
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 3. Crear el "Motor" (Engine)
# El Engine es la fábrica central de conexiones. 
# `echo=True` (opcional en desarrollo) imprimirá en consola todo el código SQL que Python genere.
# `pool_pre_ping=True` revisa si la conexión sigue viva antes de usarla (evita errores si MySQL se reinició).
engine = create_async_engine(
    DATABASE_URL,
    echo=False, # Ponlo en True si quieres ver los SELECT y UPDATEs crudos en tu consola
    pool_pre_ping=True,
    pool_size=10, # Mantiene 10 conexiones abiertas listas para usar (ideal para concurrencia)
    max_overflow=20 # Si llegan muchos chats a la vez, puede abrir hasta 20 más temporalmente
)

# 4. Crear la Fábrica de Sesiones (SessionMaker)
# Una "Sesión" es el espacio de trabajo temporal donde manipulas los datos antes de hacer "commit" (guardar)
# Usamos `async_sessionmaker` para que la espera de la base de datos libere a la CPU de Python.
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False, # Evita que los objetos se borren de la RAM de Python después de guardarlos
    autoflush=False
)

# 5. Dependencia (Generator) para inyectar en FastAPI
# Esta es una función "Yield" (Generator). Cada vez que un usuario envíe un mensaje a nuestro Webhook, 
# FastAPI pedirá una sesión de base de datos llamando a esta función.
# Al terminar de procesar el mensaje de Telegram/WA, el bloque "finally" cierra la conexión automáticamente.
async def get_db_session():
    """
    Provee una sesión de base de datos asíncrona segura.
    Debe ser usada con 'async with get_db_session() as session:'
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
