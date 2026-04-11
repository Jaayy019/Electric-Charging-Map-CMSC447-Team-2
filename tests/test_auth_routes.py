"""Tests for account creation endpoint."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "api"))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.session import Base, get_session
from database.models import User, Session, Vehicle


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
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session

    from main import app

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


VALID_ACCOUNT = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepass123",
}


@pytest.mark.asyncio
async def test_create_account_success(client):
    """POST /api/auth/create-account creates a user and returns info."""
    resp = await client.post("/api/auth/create-account", json=VALID_ACCOUNT)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_create_account_duplicate_username(client):
    """Duplicate username returns 409."""
    await client.post("/api/auth/create-account", json=VALID_ACCOUNT)
    resp = await client.post(
        "/api/auth/create-account",
        json={**VALID_ACCOUNT, "email": "other@example.com"},
    )
    assert resp.status_code == 409
    assert "Username" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_account_duplicate_email(client):
    """Duplicate email returns 409."""
    await client.post("/api/auth/create-account", json=VALID_ACCOUNT)
    resp = await client.post(
        "/api/auth/create-account",
        json={**VALID_ACCOUNT, "username": "otheruser"},
    )
    assert resp.status_code == 409
    assert "Email" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_account_short_password(client):
    """Password under 8 characters returns 400."""
    resp = await client.post(
        "/api/auth/create-account",
        json={**VALID_ACCOUNT, "password": "short"},
    )
    assert resp.status_code == 400
    assert "8 characters" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_password_is_hashed(test_session):
    """Password is stored as a hash, not plaintext."""
    from auth_routes import _hash_password, _verify_password

    hashed = _hash_password("mypassword")
    assert hashed != "mypassword"
    assert ":" in hashed
    assert _verify_password("mypassword", hashed)
    assert not _verify_password("wrongpassword", hashed)


@pytest.mark.asyncio
async def test_user_session_cascade_delete(test_session):
    """Deleting a User cascades to its Sessions."""
    from datetime import datetime, timedelta

    user = User(
        username="cascadeuser",
        email="cascade@example.com",
        password_hash="fakehash",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    session_row = Session(
        user_id=user.id,
        token="test-token-123",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    test_session.add(session_row)
    await test_session.commit()

    await test_session.delete(user)
    await test_session.commit()

    from sqlalchemy import select

    result = await test_session.execute(
        select(Session).where(Session.token == "test-token-123")
    )
    assert result.scalar_one_or_none() is None


VALID_VEHICLE = {
    "make": "Tesla",
    "model": "Model 3",
    "year": 2024,
    "port_type": "CCS",
}


async def _create_user(client):
    """Helper to create a user and return the user ID."""
    resp = await client.post("/api/auth/create-account", json=VALID_ACCOUNT)
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_add_vehicle(client):
    """POST /api/auth/users/{id}/vehicles adds a vehicle."""
    user_id = await _create_user(client)
    resp = await client.post(f"/api/auth/users/{user_id}/vehicles", json=VALID_VEHICLE)
    assert resp.status_code == 201
    data = resp.json()
    assert data["make"] == "Tesla"
    assert data["model"] == "Model 3"
    assert data["year"] == 2024
    assert data["port_type"] == "CCS"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_vehicles(client):
    """GET /api/auth/users/{id}/vehicles returns all vehicles."""
    user_id = await _create_user(client)
    await client.post(f"/api/auth/users/{user_id}/vehicles", json=VALID_VEHICLE)
    await client.post(
        f"/api/auth/users/{user_id}/vehicles",
        json={**VALID_VEHICLE, "make": "Rivian", "model": "R1T", "port_type": "CCS"},
    )
    resp = await client.get(f"/api/auth/users/{user_id}/vehicles")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_vehicles_user_not_found(client):
    """GET vehicles for non-existent user returns 404."""
    resp = await client.get("/api/auth/users/9999/vehicles")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_vehicle(client):
    """PUT /api/auth/users/{id}/vehicles/{vid} updates vehicle info."""
    user_id = await _create_user(client)
    resp = await client.post(f"/api/auth/users/{user_id}/vehicles", json=VALID_VEHICLE)
    vehicle_id = resp.json()["id"]

    updated = {**VALID_VEHICLE, "make": "Ford", "model": "Mustang Mach-E", "port_type": "CCS"}
    resp = await client.put(
        f"/api/auth/users/{user_id}/vehicles/{vehicle_id}", json=updated
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["make"] == "Ford"
    assert data["model"] == "Mustang Mach-E"


@pytest.mark.asyncio
async def test_update_vehicle_not_found(client):
    """PUT on non-existent vehicle returns 404."""
    user_id = await _create_user(client)
    resp = await client.put(
        f"/api/auth/users/{user_id}/vehicles/9999", json=VALID_VEHICLE
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_vehicle(client):
    """DELETE /api/auth/users/{id}/vehicles/{vid} removes the vehicle."""
    user_id = await _create_user(client)
    resp = await client.post(f"/api/auth/users/{user_id}/vehicles", json=VALID_VEHICLE)
    vehicle_id = resp.json()["id"]

    resp = await client.delete(f"/api/auth/users/{user_id}/vehicles/{vehicle_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/auth/users/{user_id}/vehicles")
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_vehicle_not_found(client):
    """DELETE on non-existent vehicle returns 404."""
    user_id = await _create_user(client)
    resp = await client.delete(f"/api/auth/users/{user_id}/vehicles/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_vehicle_cascade_delete(test_session):
    """Deleting a User cascades to its Vehicles."""
    user = User(
        username="vehicleuser",
        email="vehicle@example.com",
        password_hash="fakehash",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    vehicle = Vehicle(
        user_id=user.id, make="Tesla", model="Model Y",
        year=2024, port_type="CCS",
    )
    test_session.add(vehicle)
    await test_session.commit()

    await test_session.delete(user)
    await test_session.commit()

    from sqlalchemy import select

    result = await test_session.execute(
        select(Vehicle).where(Vehicle.user_id == user.id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_create_vehicle_orm(test_session):
    """Can insert and read a Vehicle via the ORM."""
    user = User(username="ormuser", email="orm@example.com", password_hash="fakehash")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    vehicle = Vehicle(
        user_id=user.id, make="Chevrolet", model="Bolt EV",
        year=2023, port_type="CCS",
    )
    test_session.add(vehicle)
    await test_session.commit()
    await test_session.refresh(vehicle)

    assert vehicle.id is not None
    assert vehicle.make == "Chevrolet"
    assert vehicle.model == "Bolt EV"
    assert vehicle.year == 2023
    assert vehicle.port_type == "CCS"
    assert vehicle.user_id == user.id
    assert vehicle.created_at is not None


@pytest.mark.asyncio
async def test_user_has_multiple_vehicles_orm(test_session):
    """A user can have multiple vehicles via the ORM."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    user = User(username="multicar", email="multi@example.com", password_hash="fakehash")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    v1 = Vehicle(user_id=user.id, make="Tesla", model="Model 3", year=2024, port_type="CCS")
    v2 = Vehicle(user_id=user.id, make="Nissan", model="Leaf", year=2022, port_type="CHAdeMO")
    v3 = Vehicle(user_id=user.id, make="Ford", model="F-150 Lightning", year=2025, port_type="CCS")
    test_session.add_all([v1, v2, v3])
    await test_session.commit()

    result = await test_session.execute(
        select(User).options(selectinload(User.vehicles)).where(User.id == user.id)
    )
    loaded_user = result.scalar_one()
    assert len(loaded_user.vehicles) == 3
    makes = {v.make for v in loaded_user.vehicles}
    assert makes == {"Tesla", "Nissan", "Ford"}


@pytest.mark.asyncio
async def test_add_vehicle_user_not_found(client):
    """POST vehicle to non-existent user returns 404."""
    resp = await client.post("/api/auth/users/9999/vehicles", json=VALID_VEHICLE)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_multiple_vehicles_same_user(client):
    """A user can add multiple vehicles via API."""
    user_id = await _create_user(client)
    vehicles = [
        {"make": "Tesla", "model": "Model 3", "year": 2024, "port_type": "CCS"},
        {"make": "Nissan", "model": "Leaf", "year": 2022, "port_type": "CHAdeMO"},
        {"make": "BMW", "model": "iX", "year": 2025, "port_type": "CCS"},
    ]
    for v in vehicles:
        resp = await client.post(f"/api/auth/users/{user_id}/vehicles", json=v)
        assert resp.status_code == 201

    resp = await client.get(f"/api/auth/users/{user_id}/vehicles")
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_update_vehicle_preserves_other_fields(client):
    """PUT updates all fields correctly."""
    user_id = await _create_user(client)
    resp = await client.post(f"/api/auth/users/{user_id}/vehicles", json=VALID_VEHICLE)
    vehicle_id = resp.json()["id"]

    updated = {"make": "Rivian", "model": "R1S", "year": 2025, "port_type": "CCS"}
    resp = await client.put(f"/api/auth/users/{user_id}/vehicles/{vehicle_id}", json=updated)
    assert resp.status_code == 200
    data = resp.json()
    assert data["make"] == "Rivian"
    assert data["model"] == "R1S"
    assert data["year"] == 2025
    assert data["port_type"] == "CCS"


@pytest.mark.asyncio
async def test_delete_one_vehicle_keeps_others(client):
    """Deleting one vehicle does not affect the user's other vehicles."""
    user_id = await _create_user(client)
    r1 = await client.post(
        f"/api/auth/users/{user_id}/vehicles",
        json={"make": "Tesla", "model": "Model Y", "year": 2024, "port_type": "CCS"},
    )
    await client.post(
        f"/api/auth/users/{user_id}/vehicles",
        json={"make": "Nissan", "model": "Leaf", "year": 2022, "port_type": "CHAdeMO"},
    )
    vid1 = r1.json()["id"]

    await client.delete(f"/api/auth/users/{user_id}/vehicles/{vid1}")
    resp = await client.get(f"/api/auth/users/{user_id}/vehicles")
    remaining = resp.json()
    assert len(remaining) == 1
    assert remaining[0]["make"] == "Nissan"


@pytest.mark.asyncio
async def test_vehicle_belongs_to_correct_user(client):
    """A user cannot access another user's vehicle."""
    # Create two users
    resp1 = await client.post("/api/auth/create-account", json={
        "username": "user_a", "email": "a@example.com", "password": "password123",
    })
    user_a = resp1.json()["id"]
    resp2 = await client.post("/api/auth/create-account", json={
        "username": "user_b", "email": "b@example.com", "password": "password123",
    })
    user_b = resp2.json()["id"]

    # Add vehicle to user_a
    resp = await client.post(f"/api/auth/users/{user_a}/vehicles", json=VALID_VEHICLE)
    vid = resp.json()["id"]

    # user_b should not see it
    resp = await client.get(f"/api/auth/users/{user_b}/vehicles")
    assert len(resp.json()) == 0

    # user_b cannot update it
    resp = await client.put(f"/api/auth/users/{user_b}/vehicles/{vid}", json=VALID_VEHICLE)
    assert resp.status_code == 404

    # user_b cannot delete it
    resp = await client.delete(f"/api/auth/users/{user_b}/vehicles/{vid}")
    assert resp.status_code == 404
