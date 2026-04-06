import os
from typing import AsyncGenerator, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()


def _strip_libpq_params_for_asyncpg(url: str) -> str:
    """Remove query keys asyncpg does not support (libpq passes sslmode, channel_binding)."""
    parsed = urlparse(url.strip())
    if not parsed.query:
        return url.strip()
    pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in ("sslmode", "channel_binding")
    ]
    return urlunparse(parsed._replace(query=urlencode(pairs)))


def resolve_database_url() -> str:
    """Prefer DATABASE_DEV_URL (Neon dev), else DATABASE_URL; empty means use SQLite."""
    dev = os.getenv("DATABASE_DEV_URL", "").strip()
    if dev:
        return dev
    return os.getenv("DATABASE_URL", "").strip()


# Base class for all ORM models
class Base(DeclarativeBase):
    pass


# Engine & session factory
_url = resolve_database_url()

if _url:
    # Remote Postgres. Neon requires TLS; asyncpg uses connect_args, not libpq sslmode.
    _url_async = _strip_libpq_params_for_asyncpg(_url)
    _pg_dsn = _url_async.removeprefix("postgresql://")
    _lower = _url.lower()
    _need_ssl = "neon.tech" in _lower or "sslmode=require" in _lower
    engine: Optional[AsyncEngine] = create_async_engine(
        "postgresql+asyncpg://" + _pg_dsn,
        pool_pre_ping=True,
        connect_args={"ssl": True} if _need_ssl else {},
    )
else:
    # Fallback to local SQLite so the app runs without Postgres
    _sqlite_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "local.db",
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
    if engine is not None:  # if the engine is not None, dispose of it
        await engine.dispose()  # dispose of the engine
