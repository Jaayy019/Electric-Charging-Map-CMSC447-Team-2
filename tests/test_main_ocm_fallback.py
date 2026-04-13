"""Tests for /api/charge-points OCM failure path and local DB fallback."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "api"))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import ChargePoint, Connection
from database.session import Base


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
async def client_ocm_patched(test_engine, monkeypatch):
    """Client where OCM is stubbed and main uses the same SQLite engine for fallback/cache."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    import main as app_main

    monkeypatch.setattr(app_main, "async_session_factory", factory)
    monkeypatch.setattr(app_main, "engine", test_engine)

    transport = ASGITransport(app=app_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_ocm_error_falls_back_to_cached_charge_points(
    test_engine, client_ocm_patched, monkeypatch
):
    """When OCM returns an error dict, response is served from the local DB if populated."""
    import main as app_main

    monkeypatch.setattr(
        app_main,
        "get_data_from_api",
        lambda *args, **kwargs: {"error": "simulated OCM failure"},
    )

    async with async_sessionmaker(test_engine, expire_on_commit=False)() as session:
        session.add(
            ChargePoint(
                id=50001,
                uuid="fallback-test-1",
                address="1 Cache Ln",
                town="Baltimore",
                postcode="21201",
                country="US",
                latitude=39.29,
                longitude=-76.61,
                number_of_points=1,
                availability="Operational",
                operator="Cached",
                connections=[
                    Connection(
                        port_type="CCS",
                        power_kw=50.0,
                        voltage=400,
                        amps=125,
                        current_type="DC",
                        status="Operational",
                        quantity=1,
                    )
                ],
            )
        )
        await session.commit()

    resp = await client_ocm_patched.get("/api/charge-points")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["total"] == 1
    assert body["data"][0]["uuid"] == "fallback-test-1"
    assert body["data"][0]["operator"] == "Cached"


@pytest.mark.asyncio
async def test_ocm_error_without_cache_returns_error(test_engine, client_ocm_patched, monkeypatch):
    """When OCM fails and the DB has no charge points, return a clear error payload."""
    import main as app_main

    monkeypatch.setattr(
        app_main,
        "get_data_from_api",
        lambda *args, **kwargs: {"error": "simulated OCM failure"},
    )

    resp = await client_ocm_patched.get("/api/charge-points")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "error"
    assert body["data"] is None
    assert "no cached data" in (body.get("error") or "").lower()
