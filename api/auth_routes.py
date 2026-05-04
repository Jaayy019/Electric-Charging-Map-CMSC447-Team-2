"""
Neon Auth (Better Auth) — backend-only integration.

Proxies sign-in / sign-up to the managed Neon Auth service and validates JWTs for
protected routes. No UI; clients call these endpoints and store the session/JWT
as needed.

Also registers local-SQLite account and vehicle routes under the same `/api/auth`
prefix (`/create-account`, `/users/.../vehicles`) for development and tests.
These paths do not overlap Neon Auth routes (`/sign-up`, `/sign-in`, `/me`).
"""

from __future__ import annotations

import hashlib
import os
from typing import Annotated, Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from database.models import User, UserVehiclePreference, Vehicle
from database.session import get_session
from models import (
    AccountCreate,
    AccountResponse,
    ChargePointSummary,
    VehicleCreate,
    VehicleResponse,
)
from neon_auth_jwt import try_decode_neon_jwt
from neon_user_sync import ensure_local_user_for_neon
from routes import query_charge_point_summaries

router = APIRouter(prefix="/api/auth", tags=["Auth"])
_bearer = HTTPBearer(auto_error=False)


def _neon_auth_base() -> str:
    return (os.getenv("NEON_AUTH_BASE_URL") or "").strip().rstrip("/")


def _require_configured() -> str:
    base = _neon_auth_base()
    if not base:
        raise HTTPException(
            status_code=503,
            detail="Neon Auth is not configured. Set NEON_AUTH_BASE_URL in the environment.",
        )
    return base


def _origin_for_neon_auth(request: Request) -> str:
    """
    Better Auth requires an Origin header on sign-up unless callbackURL is absolute.
    Browsers send Origin when calling our API from Swagger or the frontend; server-side
    clients can set NEON_AUTH_ORIGIN (e.g. http://localhost:5000).
    """
    origin = (request.headers.get("origin") or "").strip()
    if origin:
        return origin
    return (os.getenv("NEON_AUTH_ORIGIN") or "http://localhost:5000").strip()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: Optional[str] = None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


def _json_with_neon_cookies(r: httpx.Response) -> JSONResponse:
    """Forward JSON body and all Set-Cookie headers from Neon (session cookie for /me)."""
    try:
        data = r.json()
    except Exception:
        data = {"message": r.text or r.reason_phrase}
    resp = JSONResponse(content=data, status_code=r.status_code)
    for cookie in r.headers.get_list("set-cookie"):
        resp.headers.append("set-cookie", cookie)
    return resp


@router.post("/sign-up")
async def sign_up(request: Request, body: SignUpRequest) -> JSONResponse:
    """Proxy to Neon Auth `POST /sign-up/email` (Better Auth)."""
    base = _require_configured()
    # Neon Auth requires `name` default to the email local-part if omitted.
    display_name = (body.name or "").strip() or body.email.split("@", 1)[0]
    payload: dict[str, Any] = {
        "email": body.email,
        "password": body.password,
        "name": display_name,
    }
    origin = _origin_for_neon_auth(request)

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{base}/sign-up/email",
            json=payload,
            headers={"Origin": origin},
        )

    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = {"message": r.text or r.reason_phrase}
        raise HTTPException(status_code=r.status_code, detail=detail)

    return _json_with_neon_cookies(r)


@router.post("/sign-in")
async def sign_in(request: Request, body: SignInRequest) -> JSONResponse:
    """Proxy to Neon Auth `POST /sign-in/email` (Better Auth)."""
    base = _require_configured()
    payload = {"email": body.email, "password": body.password}
    origin = _origin_for_neon_auth(request)

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{base}/sign-in/email",
            json=payload,
            headers={"Origin": origin},
        )

    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = {"message": r.text or r.reason_phrase}
        raise HTTPException(status_code=r.status_code, detail=detail)

    return _json_with_neon_cookies(r)


def _looks_like_jwt(value: str) -> bool:
    return len(value.split(".")) == 3


async def get_current_user(
    request: Request,
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
) -> dict[str, Any]:
    """
    Current user from either:
    - `Authorization: Bearer <jwt>` (three dot-separated segments, verified with JWKS), or
    - Session cookies set by Neon on sign-in/sign-up (forwarded in our JSON response).

    The opaque `token` string in the JSON body is **not** a JWT; it cannot be used as Bearer.
    """
    base = _neon_auth_base()
    if not base:
        raise HTTPException(
            status_code=503,
            detail="Neon Auth is not configured. Set NEON_AUTH_BASE_URL in the environment.",
        )

    if creds is not None and creds.scheme.lower() == "bearer":
        raw = creds.credentials.strip()
        if _looks_like_jwt(raw):
            payload, err = try_decode_neon_jwt(raw)
            if payload is None:
                raise HTTPException(status_code=401, detail=f"Invalid JWT: {err}")
            return {"user": payload}

        raise HTTPException(
            status_code=401,
            detail=(
                "Bearer token is not a JWT (expected three segments like eyJ...). "
                "The sign-in `token` field is an opaque session id. "
                "Clear Authorization in Swagger; call GET /api/auth/me with cookies from sign-in, "
                "or use a JWT if Neon Auth JWT plugin is enabled."
            ),
        )

    cookie = (request.headers.get("cookie") or "").strip()
    if not cookie:
        raise HTTPException(
            status_code=401,
            detail=(
                "Missing session. Sign in first, then GET /api/auth/me without Bearer (cookies), "
                "or use Authorization: Bearer <jwt>."
            ),
        )

    origin = _origin_for_neon_auth(request)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{base}/get-session",
            headers={"Origin": origin, "Cookie": cookie},
        )

    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    data = r.json()
    if not data or not isinstance(data, dict):
        raise HTTPException(status_code=401, detail="No session")

    user = data.get("user")
    if user is None:
        raise HTTPException(status_code=401, detail="No user in session")

    out: dict[str, Any] = {"user": user}
    if data.get("session") is not None:
        out["session"] = data["session"]
    return out


@router.get("/me")
async def me(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
    """Session user (cookie) or JWT claims (Bearer), depending on how you authenticated."""
    return user


@router.post("/sign-out")
async def sign_out() -> dict[str, str]:
    """
    Sign-out clears server-side session cookies on Neon Auth; for Bearer/JWT
    clients the client should discard the token.

    TODO(backend): forward Cookie to Neon Auth /sign-out when using cookie sessions.
    """
    return {
        "status": "ok",
        "message": ("Discard client-side token. Cookie sign-out can be added with the frontend."),
    }


# --- Authenticated mirror user (Neon Auth JWT/session -> local User for vehicles & stations) ---


async def get_local_user_from_neon(
    current: Annotated[dict[str, Any], Depends(get_current_user)],
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        return await ensure_local_user_for_neon(session, current)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def _get_active_vehicle_id(session: AsyncSession, user_id: int) -> int | None:
    pref = await session.get(UserVehiclePreference, user_id)
    return pref.active_vehicle_id if pref else None


def _vehicle_response(v: Vehicle, *, active_id: int | None) -> VehicleResponse:
    return VehicleResponse(
        id=v.id,
        make=v.make,
        model=v.model,
        year=v.year,
        port_type=v.port_type,
        created_at=v.created_at,
        is_active=(active_id is not None and v.id == active_id),
    )


@router.get("/me/vehicles", response_model=list[VehicleResponse])
async def me_list_vehicles(
    user: Annotated[User, Depends(get_local_user_from_neon)],
    session: AsyncSession = Depends(get_session),
):
    """List vehicles for the authenticated Neon user (mirrored local account)."""
    active_id = await _get_active_vehicle_id(session, user.id)
    result = await session.execute(select(Vehicle).where(Vehicle.user_id == user.id))
    rows = result.scalars().all()
    return [_vehicle_response(v, active_id=active_id) for v in rows]


@router.post("/me/vehicles", response_model=VehicleResponse, status_code=201)
async def me_add_vehicle(
    data: VehicleCreate,
    user: Annotated[User, Depends(get_local_user_from_neon)],
    session: AsyncSession = Depends(get_session),
):
    """Add a vehicle to the authenticated user's account."""
    vehicle = Vehicle(
        user_id=user.id,
        make=data.make,
        model=data.model,
        year=data.year,
        port_type=data.port_type,
    )
    session.add(vehicle)
    await session.commit()
    await session.refresh(vehicle)
    active_id = await _get_active_vehicle_id(session, user.id)
    return _vehicle_response(vehicle, active_id=active_id)


@router.put("/me/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def me_update_vehicle(
    vehicle_id: int,
    data: VehicleCreate,
    user: Annotated[User, Depends(get_local_user_from_neon)],
    session: AsyncSession = Depends(get_session),
):
    """Update a vehicle owned by the authenticated user."""
    result = await session.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.user_id == user.id)
    )
    vehicle = result.scalar_one_or_none()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    vehicle.make = data.make
    vehicle.model = data.model
    vehicle.year = data.year
    vehicle.port_type = data.port_type
    await session.commit()
    await session.refresh(vehicle)
    active_id = await _get_active_vehicle_id(session, user.id)
    return _vehicle_response(vehicle, active_id=active_id)


@router.delete("/me/vehicles/{vehicle_id}", status_code=204)
async def me_delete_vehicle(
    vehicle_id: int,
    user: Annotated[User, Depends(get_local_user_from_neon)],
    session: AsyncSession = Depends(get_session),
):
    """Delete a vehicle owned by the authenticated user."""
    result = await session.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.user_id == user.id)
    )
    vehicle = result.scalar_one_or_none()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    await session.delete(vehicle)
    await session.commit()


@router.put("/me/vehicles/{vehicle_id}/active", response_model=VehicleResponse)
async def me_set_active_vehicle(
    vehicle_id: int,
    user: Annotated[User, Depends(get_local_user_from_neon)],
    session: AsyncSession = Depends(get_session),
):
    """Mark a saved vehicle as active for connector filtering / station queries."""
    result = await session.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.user_id == user.id)
    )
    vehicle = result.scalar_one_or_none()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    pref = await session.get(UserVehiclePreference, user.id)
    if pref is None:
        pref = UserVehiclePreference(user_id=user.id, active_vehicle_id=vehicle.id)
        session.add(pref)
    else:
        pref.active_vehicle_id = vehicle.id
    await session.commit()
    await session.refresh(vehicle)
    return _vehicle_response(vehicle, active_id=vehicle.id)


@router.get("/me/charge-points", response_model=list[ChargePointSummary])
async def me_list_charge_points(
    user: Annotated[User, Depends(get_local_user_from_neon)],
    session: AsyncSession = Depends(get_session),
    latitude: Optional[float] = Query(None, description="Map click / center latitude"),
    longitude: Optional[float] = Query(None, description="Map click / center longitude"),
    radius_km: Optional[float] = Query(
        None, description="Search radius in km (default 10 if lat/lng set)"
    ),
    vehicle_id: Optional[int] = Query(
        None,
        description="Use this saved vehicle for compatibility; defaults to active vehicle",
    ),
    port_type: Optional[str] = Query(
        None,
        description="Optional connector filter when no vehicle context",
    ),
    min_power_kw: Optional[float] = Query(None, ge=0),
    operational_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Charge points compatible with the user's active vehicle (or selected vehicle_id).

    When no active vehicle and vehicle_id is omitted, results are not filtered by connector
    unless `port_type` is provided.
    """
    active = await _get_active_vehicle_id(session, user.id)
    vid = vehicle_id if vehicle_id is not None else active
    return await query_charge_point_summaries(
        session,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        port_type=port_type,
        vehicle_id=vid,
        vehicle_owner_user_id=user.id,
        min_power_kw=min_power_kw,
        operational_only=operational_only,
        limit=limit,
        offset=offset,
    )


# --- Local SQLite account / vehicle (development & tests; distinct from Neon paths) ---


def _hash_password(password: str) -> str:
    """Hash a password with a random salt using PBKDF2-SHA256."""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=600_000)
    return salt.hex() + ":" + hashed.hex()


def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored hash."""
    salt_hex, hash_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=600_000)
    return hashed.hex() == hash_hex


@router.post("/create-account", response_model=AccountResponse, status_code=201)
async def create_account(
    data: AccountCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new user account in the local database."""
    if not data.username or not data.email or not data.password:
        raise HTTPException(status_code=400, detail="All fields are required")

    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = await session.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Username already taken")

    existing = await session.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=_hash_password(data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return AccountResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
    )


@router.get("/users/{user_id}/vehicles", response_model=list[VehicleResponse])
async def list_vehicles(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """List all vehicles for a user."""
    user = await session.execute(select(User).where(User.id == user_id))
    if user.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await session.execute(select(Vehicle).where(Vehicle.user_id == user_id))
    rows = result.scalars().all()
    return [
        VehicleResponse(
            id=v.id,
            make=v.make,
            model=v.model,
            year=v.year,
            port_type=v.port_type,
            created_at=v.created_at,
        )
        for v in rows
    ]


@router.post("/users/{user_id}/vehicles", response_model=VehicleResponse, status_code=201)
async def add_vehicle(
    user_id: int,
    data: VehicleCreate,
    session: AsyncSession = Depends(get_session),
):
    """Add a vehicle to a user's account."""
    user = await session.execute(select(User).where(User.id == user_id))
    if user.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")

    vehicle = Vehicle(
        user_id=user_id,
        make=data.make,
        model=data.model,
        year=data.year,
        port_type=data.port_type,
    )
    session.add(vehicle)
    await session.commit()
    await session.refresh(vehicle)

    return VehicleResponse(
        id=vehicle.id,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        port_type=vehicle.port_type,
        created_at=vehicle.created_at,
    )


@router.put("/users/{user_id}/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    user_id: int,
    vehicle_id: int,
    data: VehicleCreate,
    session: AsyncSession = Depends(get_session),
):
    """Update a vehicle's info."""
    result = await session.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.user_id == user_id)
    )
    vehicle = result.scalar_one_or_none()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    vehicle.make = data.make
    vehicle.model = data.model
    vehicle.year = data.year
    vehicle.port_type = data.port_type
    await session.commit()
    await session.refresh(vehicle)

    return VehicleResponse(
        id=vehicle.id,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        port_type=vehicle.port_type,
        created_at=vehicle.created_at,
    )


@router.delete("/users/{user_id}/vehicles/{vehicle_id}", status_code=204)
async def delete_vehicle(
    user_id: int,
    vehicle_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a vehicle from a user's account."""
    result = await session.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.user_id == user_id)
    )
    vehicle = result.scalar_one_or_none()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    await session.delete(vehicle)
    await session.commit()
