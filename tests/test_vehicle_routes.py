"""Tests for /api/vehicle catalog routes (API Ninjas + VEHICLE_API_KEY)."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "api"))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.session import Base, get_session


@pytest_asyncio.fixture()
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def vclient(test_engine, monkeypatch):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session

    monkeypatch.setenv("VEHICLE_API_KEY", "test-api-key-for-ci")

    from main import app

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_electric_vehicles_requires_filter_when_key_set(vclient):
    """API Ninjas expects at least one filter parameter."""
    resp = await vclient.get("/api/vehicle/electric-vehicles")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_electric_vehicles_missing_api_key_returns_503(test_engine, monkeypatch):
    monkeypatch.delenv("VEHICLE_API_KEY", raising=False)

    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session

    from main import app

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/vehicle/electric-makes")

    app.dependency_overrides.clear()
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_electric_makes_proxies_api_ninjas(vclient, monkeypatch):
    fake = AsyncMock(return_value=[{"name": "Tesla"}])
    monkeypatch.setattr(
        "vehicle_routes.ninjas_get_json",
        fake,
    )

    resp = await vclient.get("/api/vehicle/electric-makes")
    assert resp.status_code == 200
    assert resp.json() == [{"name": "Tesla"}]
    fake.assert_awaited_once()


@pytest.mark.asyncio
async def test_electric_vehicles_calls_ninjas_with_params(vclient, monkeypatch):
    fake = AsyncMock(return_value=[{"make": "nissan", "model": "leaf"}])
    monkeypatch.setattr(
        "vehicle_routes.ninjas_get_json",
        fake,
    )

    resp = await vclient.get(
        "/api/vehicle/electric-vehicles",
        params={"make": "nissan"},
    )
    assert resp.status_code == 200
    fake.assert_awaited_once()
    assert fake.await_args.args[0] == "electricvehicle"
    assert fake.await_args.args[1]["make"] == "nissan"
