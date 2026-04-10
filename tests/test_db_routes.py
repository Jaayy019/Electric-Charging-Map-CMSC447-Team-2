"""Tests for database session, models, and CRUD routes using an in-memory SQLite backend."""

import sys
from pathlib import Path

# Make sure repo root and api/ are on the path
_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "api"))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from api.routes import _bounding_box, _haversine_km
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from database.session import Base, get_session
from database.models import ChargePoint, Connection

# Fixtures — spin up an in-memory SQLite DB for each test


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
async def test_session(test_engine):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture()
async def client(test_engine):
    """Provide an HTTPX AsyncClient wired to the FastAPI app with a test DB."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session

    # Import app here so env isn't required at collection time
    from api.main import app

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Sample

SAMPLE_CHARGE_POINT = {
    "id": 12345,
    "uuid": "test-uuid-001",
    "location": {
        "address": "123 Main St",
        "town": "Springfield",
        "postcode": "12345",
        "country": "US",
        "latitude": 39.7817,
        "longitude": -89.6501,
        "contact_email": "test@example.com",
    },
    "connections": [
        {
            "id": 1,
            "port_type": "Type 2",
            "power_kw": 22.0,
            "voltage": 230,
            "amps": 32,
            "current_type": "AC (Three-Phase)",
            "status": "Operational",
            "quantity": 2,
        }
    ],
    "number_of_points": 2,
    "price": "$0.30/kWh",
    "availability": "Operational",
    "membership_required": False,
    "access_key_required": False,
    "operator": "TestOperator",
    "last_verified": None,
}


# ORM model tests


@pytest.mark.asyncio
async def test_create_charge_point_orm(test_session):
    """Can insert and read a ChargePoint via the ORM."""
    cp = ChargePoint(
        id=1,
        uuid="orm-test-1",
        address="1 Test Rd",
        town="TestTown",
        postcode="00000",
        country="US",
        latitude=40.0,
        longitude=-75.0,
        number_of_points=1,
        availability="Operational",
        operator="Op",
        connections=[
            Connection(
                id=1,
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
    test_session.add(cp)
    await test_session.commit()


    result = await test_session.execute(
        select(ChargePoint)
        .options(selectinload(ChargePoint.connections))
        .where(ChargePoint.id == 1)
    )
    row = result.scalar_one()
    assert row.uuid == "orm-test-1"
    assert len(row.connections) == 1
    assert row.connections[0].port_type == "CCS"


@pytest.mark.asyncio
async def test_cascade_delete(test_session):
    """Deleting a ChargePoint cascades to its Connections."""
    cp = ChargePoint(
        id=2,
        uuid="cascade-test",
        address="",
        town="",
        postcode="",
        country="US",
        latitude=0.0,
        longitude=0.0,
        number_of_points=0,
        availability="Unknown",
        operator="X",
        connections=[
            Connection(
                id=10,
                port_type="Type1",
                power_kw=7.0,
                voltage=230,
                amps=32,
                current_type="AC",
                status="Operational",
                quantity=1,
            )
        ],
    )
    test_session.add(cp)
    await test_session.commit()

    await test_session.delete(cp)
    await test_session.commit()

    result = await test_session.execute(select(Connection).where(Connection.id == 10))
    assert result.scalar_one_or_none() is None


# Route tests


@pytest.mark.asyncio
async def test_list_empty(client):
    """GET /api/db/charge-points returns empty list initially."""
    resp = await client.get("/api/db/charge-points")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_and_get(client):
    """POST then GET a charge point."""
    # Create
    resp = await client.post("/api/db/charge-points", json=SAMPLE_CHARGE_POINT)
    assert resp.status_code == 201
    data = resp.json()
    assert data["uuid"] == "test-uuid-001"
    assert len(data["connections"]) == 1

    # Get by ID
    resp = await client.get(f"/api/db/charge-points/{data['id']}")
    assert resp.status_code == 200
    assert resp.json()["operator"] == "TestOperator"


@pytest.mark.asyncio
async def test_bulk_create(client):
    """POST /api/db/charge-points/bulk saves multiple."""
    items = [
        {**SAMPLE_CHARGE_POINT, "id": 100 + i, "uuid": f"bulk-{i}", "connections": []}
        for i in range(3)
    ]
    resp = await client.post("/api/db/charge-points/bulk", json=items)
    assert resp.status_code == 201
    assert resp.json()["saved"] == 3

    # Verify they're in the DB
    resp = await client.get("/api/db/charge-points?limit=10")
    assert len(resp.json()) >= 3


@pytest.mark.asyncio
async def test_delete(client):
    """DELETE removes a charge point."""
    # Create first
    resp = await client.post(
        "/api/db/charge-points",
        json={**SAMPLE_CHARGE_POINT, "id": 999, "uuid": "del-test"},
    )
    assert resp.status_code == 201

    # Delete
    resp = await client.delete("/api/db/charge-points/999")
    assert resp.status_code == 204

    # Confirm gone
    resp = await client.get("/api/db/charge-points/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_not_found(client):
    """GET nonexistent ID returns 404."""
    resp = await client.get("/api/db/charge-points/0")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health(client):
    """Health endpoint still works."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_openapi_schema(client):
    """OpenAPI JSON exposes health, external OCM proxy, and DB routes."""
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json().get("paths", {})
    assert "/health" in paths
    assert "/api/charge-points" in paths
    assert "/api/db/charge-points" in paths


@pytest.mark.asyncio
async def test_swagger_ui(client):
    """Swagger UI is served for interactive API exploration."""
    resp = await client.get("/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower()


@pytest.mark.asyncio
async def test_geo_filter_returns_only_stations_in_radius(client):
    """Stations inside the search radius are returned, stations outside are excluded."""
    #Baltimore City Hall — reference point for the search
    center_lat, center_lng = 39.2904, -76.6111

    #Base payload with no connection IDs to avoid unique constraint collisions
    base = {**SAMPLE_CHARGE_POINT, "connections": []}
    
    #Not real charge points, just used for testing
    #Station A: ~1 km north (should be included in a 5 km search)
    station_near = {**base, "id": 201, "uuid": "geo-near", "location": 
    {**SAMPLE_CHARGE_POINT["location"],
    "latitude": 39.2994, 
    "longitude": -76.6122}}

    #Station B: ~36 km away (Annapolis should be excluded by a 5 km radius)
    station_far = {**base, "id": 202, "uuid": "geo-far","location": 
    {**SAMPLE_CHARGE_POINT["location"],
    "latitude": 38.9784, 
    "longitude": -76.4922}}

    await client.post("/api/db/charge-points", json=station_near)
    await client.post("/api/db/charge-points", json=station_far)

    resp = await client.get(
        "/api/db/charge-points",
        params={"latitude": center_lat, "longitude": center_lng, "radius_km": 5},
    )
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()]
    assert 201 in ids, "Near station should be included"
    assert 202 not in ids, "Far station (Annapolis) should be excluded"


@pytest.mark.asyncio
async def test_geo_filter_no_results_when_all_out_of_radius(client):
    """Returns empty list when no stations fall within the search radius."""
    #Station in San Francisco no connection IDs to avoid collisions
    station_sf = {**SAMPLE_CHARGE_POINT, "id": 203, "uuid": "geo-sf", "connections": [],"location": 
    {**SAMPLE_CHARGE_POINT["location"],
    "latitude": 37.7749, 
    "longitude": -122.4194}}
    await client.post("/api/db/charge-points", json=station_sf)

    #Search around Baltimore with a 10 km radius to verify it's working
    resp = await client.get(
        "/api/db/charge-points",
        params={"latitude": 39.2904, "longitude": -76.6122, "radius_km": 10},
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_geo_filter_missing_params_returns_all(client):
    """When geo params are omitted entirely, all charge points are returned (no filter)."""
    station = {**SAMPLE_CHARGE_POINT, "id": 204, "uuid": "geo-nofilter", "connections": []}
    await client.post("/api/db/charge-points", json=station)

    #No geo params should return everything
    resp = await client.get("/api/db/charge-points")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_geo_filter_partial_params_ignored(client):
    """Supplying lat+lng but no radius_km falls back to returning all rows (no filter)."""
    station = {**SAMPLE_CHARGE_POINT, "id": 205, "uuid": "geo-partial", "connections": []}
    await client.post("/api/db/charge-points", json=station)

    #lat+lng but no radius treated as no geo filter
    resp = await client.get(
        "/api/db/charge-points",
        params={"latitude": 39.2904, "longitude": -76.6122},
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

# Haversine / bounding-box unit tests

def test_haversine_known_distance():
    """Haversine between Baltimore City Hall and Annapolis State House is ~36 km."""
    dist = _haversine_km(39.2904, -76.6111, 38.9784, -76.4922)
    assert 34 < dist < 40, f"Expected ~36 km, got {dist:.2f}"


def test_haversine_zero_distance():
    """Same point should return 0 km."""
    assert _haversine_km(39.0, -76.0, 39.0, -76.0) == 0.0


def test_bounding_box_symmetry():
    """Bounding box should be symmetric around the centre point."""
    lat, lon, r = 39.2904, -76.6122, 10.0
    min_lat, max_lat, min_lon, max_lon = _bounding_box(lat, lon, r)
    assert min_lat < lat < max_lat
    assert min_lon < lon < max_lon
    #Lat delta is constant (~ r / 111.32)
    assert pytest.approx(max_lat - lat, abs=0.01) == lat - min_lat
