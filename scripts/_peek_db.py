"""Helper script: print row counts (run from repo root). Not for production."""

import asyncio
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from dotenv import load_dotenv
from sqlalchemy import func, select

load_dotenv()

from database.models import ChargePoint, Connection
from database.session import async_session_factory


async def main() -> None:
    async with async_session_factory() as session:
        cp = (await session.execute(select(func.count()).select_from(ChargePoint))).scalar_one()
        cn = (await session.execute(select(func.count()).select_from(Connection))).scalar_one()
        sample = (
            await session.execute(select(ChargePoint.town, ChargePoint.country).limit(5))
        ).all()
        print("charge_points:", cp)
        print("connections:", cn)
        print("sample towns/countries:", list(sample))


if __name__ == "__main__":
    asyncio.run(main())
