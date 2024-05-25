from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

from config import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, DB_PORT
from models import meta


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)


async def recreate_tables():
    async with engine.begin() as conn:
        await conn.run_sync(meta.drop_all)
        await conn.run_sync(meta.create_all)


async def check_db():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        print(e)
        exit(1)


engine = create_async_engine(f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
