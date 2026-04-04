import os
from typing import AsyncGenerator, Optional

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

#Get the url from the environment variable and create the engine

# Base class for all ORM models
class Base(DeclarativeBase):
    pass

# Engine & session factory
_url = os.getenv("DATABASE_URL", "").strip()

if _url:
    # Remote Postgres
    engine: Optional[AsyncEngine] = create_async_engine(
        "postgresql+asyncpg://" + _url.removeprefix("postgresql://"), #remove the postgresql:// from the url
        pool_pre_ping=True, #ping the database to keep the connection alive
    )
else:
    # Fallback to local SQLite so the app runs without Postgres
    _sqlite_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "local.db",
    )
    os.makedirs(os.path.dirname(_sqlite_path), exist_ok=True)
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{_sqlite_path}",
        echo=False,
    )

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


# FastAPI dependency — yields one session per request
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def dispose_engine() -> None:
    if engine is not None: #if the engine is not None, dispose of it
        await engine.dispose() #dispose of the engine
