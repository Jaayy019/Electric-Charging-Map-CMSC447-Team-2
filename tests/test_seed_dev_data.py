"""Tests for dev seed charge-point payloads (same data as scripts/seed_dev_db.py)."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from database.models import ChargePoint
from database.seed_dev_samples import get_dev_seed_charge_points
from database.session import Base


def test_dev_seed_charge_points_shape():
    """Seed payload matches the two demo stations (ids, uuids, connection counts)."""
    samples = get_dev_seed_charge_points()
    assert len(samples) == 2
    assert samples[0].id == 10001
    assert samples[0].uuid == "seed-demo-001"
    assert samples[0].town == "Baltimore"
    assert samples[0].operator == "Demo Energy"
    assert len(samples[0].connections) == 2
    assert samples[0].connections[0].port_type == "CCS"
    assert samples[0].connections[1].port_type == "J1772"

    assert samples[1].id == 10002
    assert samples[1].uuid == "seed-demo-002"
    assert samples[1].contact_email == "support@example.com"
    assert samples[1].membership_required is True
    assert len(samples[1].connections) == 1
    assert samples[1].connections[0].port_type == "CHAdeMO"


@pytest_asyncio.fixture()
async def sqlite_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_dev_seed_persists_and_round_trips(sqlite_engine):
    """Dev seed ORM rows can be inserted into SQLite and read back."""
    factory = async_sessionmaker(sqlite_engine, expire_on_commit=False)
    samples = get_dev_seed_charge_points()
    async with factory() as session:
        for cp in samples:
            session.add(cp)
        await session.commit()

    async with factory() as session:
        n = await session.scalar(select(func.count()).select_from(ChargePoint))
        assert n == 2
        result = await session.execute(
            select(ChargePoint)
            .options(selectinload(ChargePoint.connections))
            .order_by(ChargePoint.id)
        )
        rows = result.scalars().all()

    assert [r.id for r in rows] == [10001, 10002]
    assert rows[0].latitude == pytest.approx(39.2555)
    assert len(rows[0].connections) == 2
    assert len(rows[1].connections) == 1
