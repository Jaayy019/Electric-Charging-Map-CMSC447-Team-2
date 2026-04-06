#!/usr/bin/env python3
"""Create tables (if needed) and insert sample charge points into the configured database.

Uses DATABASE_DEV_URL if set, otherwise DATABASE_URL (same rules as database/session.py).
Run from repo root: python scripts/seed_dev_db.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Repo root on path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")

from sqlalchemy import func, select

from database.models import ChargePoint
from database.seed_dev_samples import get_dev_seed_charge_points
from database.session import Base, async_session_factory, resolve_database_url


async def main() -> int:
    url = resolve_database_url()
    if not url:
        print(
            "error: set DATABASE_DEV_URL or DATABASE_URL in .env (or export in shell).",
            file=sys.stderr,
        )
        return 1

    from database.session import engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session_factory() as session:
            n = await session.scalar(select(func.count()).select_from(ChargePoint))
            if n and n > 0:
                print(f"Database already has {n} charge point(s); skipping seed.")
                return 0

            samples = get_dev_seed_charge_points()
            for cp in samples:
                session.add(cp)
            await session.commit()
            print(f"Seeded {len(samples)} charge points (ids {samples[0].id}, {samples[1].id}).")
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
