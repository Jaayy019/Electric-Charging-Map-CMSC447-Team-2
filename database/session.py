import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

load_dotenv()

#Get the url from the environment variable and create the engine
_url = os.getenv("DATABASE_URL", "").strip()
engine: Optional[AsyncEngine] = (
    create_async_engine(
        "postgresql+asyncpg://" + _url.removeprefix("postgresql://"), #remove the postgresql:// from the url
        pool_pre_ping=True, #ping the database to keep the connection alive
    )
    if _url
    else None
)


async def dispose_engine() -> None:
    if engine is not None: #if the engine is not None, dispose of it
        await engine.dispose() #dispose of the engine
