import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

async def create_db():
    # Connect to the MySQL server without specifying a database
    engine = create_async_engine(
        "mysql+aiomysql://root:@127.0.0.1:3306/",
        isolation_level="AUTOCOMMIT"
    )
    
    async with engine.connect() as conn:
        print("Creating database comm_agent_test...")
        await conn.execute(sa.text("CREATE DATABASE IF NOT EXISTS comm_agent_test;"))
        print("Database comm_agent_test created successfully!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_db())
