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

from database.models import ChargePoint, Connection
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

            samples = [
                ChargePoint(
                    id=10001,
                    uuid="seed-demo-001",
                    address="1000 Hilltop Cir",
                    town="Baltimore",
                    postcode="21250",
                    country="US",
                    latitude=39.2555,
                    longitude=-76.7105,
                    contact_email=None,
                    number_of_points=4,
                    price="$0.35/kWh",
                    availability="Operational",
                    membership_required=False,
                    access_key_required=False,
                    operator="Demo Energy",
                    last_verified=None,
                    connections=[
                        Connection(
                            port_type="CCS",
                            power_kw=150.0,
                            voltage=400,
                            amps=375,
                            current_type="DC",
                            status="Operational",
                            quantity=2,
                        ),
                        Connection(
                            port_type="J1772",
                            power_kw=7.2,
                            voltage=240,
                            amps=30,
                            current_type="AC",
                            status="Operational",
                            quantity=2,
                        ),
                    ],
                ),
                ChargePoint(
                    id=10002,
                    uuid="seed-demo-002",
                    address="1 Main St",
                    town="Columbia",
                    postcode="21044",
                    country="US",
                    latitude=39.2037,
                    longitude=-76.8610,
                    contact_email="support@example.com",
                    number_of_points=2,
                    price=None,
                    availability="Operational",
                    membership_required=True,
                    access_key_required=False,
                    operator="Other Op",
                    last_verified=None,
                    connections=[
                        Connection(
                            port_type="CHAdeMO",
                            power_kw=50.0,
                            voltage=500,
                            amps=125,
                            current_type="DC",
                            status="Operational",
                            quantity=1,
                        ),
                    ],
                ),
            ]

            for cp in samples:
                session.add(cp)
            await session.commit()
            print(f"Seeded {len(samples)} charge points (ids {samples[0].id}, {samples[1].id}).")
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
