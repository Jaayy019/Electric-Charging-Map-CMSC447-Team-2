from contextlib import asynccontextmanager
import asyncio
import logging
import math
import os
import sys
from pathlib import Path

# Repo root on path so database package resolves when running from api/
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from api_get import get_data_from_api, transform_to_simplified_schema
from models import ChargePointSummary
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import dispose_engine, engine, async_session_factory, ChargePoint, Connection
from database.session import Base
from auth_routes import router as auth_router
from routes import router as db_router, charge_point_to_summary
from vehicle_routes import router as vehicle_router

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration — must match .env.example (`OCM_API_KEY`); `API_KEY` kept as legacy alias
OCM_API_KEY = os.getenv("OCM_API_KEY") or os.getenv("API_KEY")
EXTERNAL_API_URL = "https://api.openchargemap.io/v3/poi/"
USER_AGENT = "MyApp/1.0"


# If the app is shutdown, dispose the engine.
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Create tables if the database is configured
    if engine is not None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await dispose_engine()


# Initialize FastAPI app
app = FastAPI(
    title="Charge Point API",
    description="A simplified backend API for charge point data",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: explicit origins required when allow_credentials=True (cannot use "*").
_cors = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define response models
class DataResponse(BaseModel):
    status: str
    data: Optional[List[ChargePointSummary]] = None
    total: int = 0
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns the great-circle distance in km between two lat/lng points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def _query_db_by_radius(
    lat: float, lng: float, distance_km: float
) -> List[ChargePointSummary]:
    """
    Query Neon for charge points within distance_km of the given coordinates.
    Uses a bounding-box pre-filter then Haversine for accuracy.
    Returns an empty list if the engine is not configured.
    """
    if engine is None:
        return []

    # Bounding box approximation — 1 degree lat ≈ 111 km
    deg_margin = distance_km / 111.0

    async with async_session_factory() as session:

        stmt = (
            select(ChargePoint)
            .options(selectinload(ChargePoint.connections))
            .where(ChargePoint.latitude.between(lat - deg_margin, lat + deg_margin))
            .where(ChargePoint.longitude.between(lng - deg_margin, lng + deg_margin))
        )

        result = await session.execute(stmt)
        rows = result.scalars().all()

    # Haversine exact filter — bounding box includes corners that are too far
    return [
        charge_point_to_summary(r)
        for r in rows
        if _haversine_km(lat, lng, r.latitude, r.longitude) <= distance_km
    ]


async def _save_to_local_db(charge_points: List[ChargePointSummary]) -> int:
    """Persist charge points to the local database, skipping duplicates by ID."""
    if engine is None:
        return 0

    saved = 0
    async with async_session_factory() as session:

        for cp in charge_points:

            existing = await session.execute(
                select(ChargePoint).where(ChargePoint.id == cp.id)
            )
            if existing.scalar_one_or_none() is not None:
                continue

            row = ChargePoint(
                id=cp.id,
                uuid=cp.uuid,
                address=cp.location.address,
                town=cp.location.town,
                postcode=cp.location.postcode,
                country=cp.location.country,
                latitude=cp.location.latitude,
                longitude=cp.location.longitude,
                contact_email=cp.location.contact_email,
                number_of_points=cp.number_of_points,
                price=cp.price,
                availability=cp.availability,
                membership_required=cp.membership_required,
                access_key_required=cp.access_key_required,
                operator=cp.operator,
                last_verified=cp.last_verified,
                connections=[
                    Connection(
                        id=c.id,
                        port_type=c.port_type,
                        power_kw=c.power_kw,
                        voltage=c.voltage,
                        amps=c.amps,
                        current_type=c.current_type,
                        status=c.status,
                        quantity=c.quantity,
                    )
                    for c in cp.connections
                ],
            )
            session.add(row)
            saved += 1

        if saved:
            await session.commit()

    return saved


async def _fetch_and_save_from_ocm(params: dict) -> Optional[List[ChargePointSummary]]:
    """
    Fetches from the OCM API, saves new stations to Neon, and returns
    the simplified data. Returns None on error.
    """
    result = get_data_from_api(OCM_API_KEY, EXTERNAL_API_URL, USER_AGENT, params)

    if isinstance(result, dict) and "error" in result:
        logger.warning("OCM API error: %s", result.get("error"))
        return None

    simplified_data, transform_error = transform_to_simplified_schema(result)

    if simplified_data is None:
        logger.warning("Transform failed: %s", transform_error)
        return None

    try:
        saved_count = await _save_to_local_db(simplified_data)
        if saved_count:
            logger.info("Saved %s new charge point(s) to Neon", saved_count)
    except Exception:
        logger.exception("Failed to save to local database")

    return simplified_data


@app.get("/api/charge-points", response_model=DataResponse, tags=["Charge Points"])
async def get_charge_points(

    latitude: Optional[float] = Query(None, description="Latitude for location-based search"),
    longitude: Optional[float] = Query(None, description="Longitude for location-based search"),
    distance: Optional[int] = Query(
        None,
        description="Search radius in kilometers (default: 5km if lat/lng provided)",
    ),

):
    """
    Returns charge points using a database-first strategy:
      1. Query Neon for stations within the requested radius.
      2. If Neon has results, return them immediately and refresh from OCM in the background.
      3. If Neon is empty for this area, fetch from OCM, save, and return.

    Falls back to any cached Neon data if OCM is unreachable.
    """
    dist_km = distance if distance is not None else 5

    # try the database first
    if latitude is not None and longitude is not None:

        logger.info(
            "DB-first search: lat=%s lng=%s distance=%skm", latitude, longitude, dist_km
        )

        db_results = await _query_db_by_radius(latitude, longitude, dist_km)

        if db_results:

            logger.info("Returning %s stations from Neon cache", len(db_results))

            # Kick off an OCM refresh in the background so new stations get saved
            ocm_params = {
                "latitude": latitude,
                "longitude": longitude,
                "distance": dist_km,
                "distanceunit": "KM",
                "maxresults": 1000,
                "verbose": "false",
                "key": OCM_API_KEY,
            }
            asyncio.create_task(_fetch_and_save_from_ocm(ocm_params))

            return DataResponse(
                status="success",
                data=db_results,
                total=len(db_results),
                error=None,
            )

    # Neon had nothing - fetch from OCM 
    logger.info("No DB results for this area, fetching from OCM")

    ocm_params: dict = {
        "distanceunit": "KM",
        "maxresults": 1000,
        "verbose": "false",
        "key": OCM_API_KEY,
    }

    if latitude is not None and longitude is not None:
        ocm_params["latitude"] = latitude
        ocm_params["longitude"] = longitude
        ocm_params["distance"] = dist_km

    simplified_data = await _fetch_and_save_from_ocm(ocm_params)

    if simplified_data is None:
        # OCM also failed, try the fallback
        logger.warning("OCM failed, returning fallback from Neon")
        return await _fallback_from_local_db()

    return DataResponse(
        status="success",
        data=simplified_data,
        total=len(simplified_data),
        error=None,
    )


async def _fallback_from_local_db() -> DataResponse:
    """Serve cached charge points from Neon when the external API is unavailable."""
    if engine is None:
        return DataResponse(status="error", data=None, total=0, error="No database configured")

    try:

        async with async_session_factory() as session:

            stmt = (
                select(ChargePoint)
                .options(selectinload(ChargePoint.connections))
                .limit(100)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

            if not rows:
                return DataResponse(
                    status="error",
                    data=None,
                    total=0,
                    error="External API unavailable and no cached data found",
                )

            data = [charge_point_to_summary(r) for r in rows]
            return DataResponse(status="success", data=data, total=len(data), error=None)

    except Exception as e:
        return DataResponse(
            status="error",
            data=None,
            total=0,
            error=f"External API unavailable and database fallback failed: {e}",
        )


# Mount database-backed routes
app.include_router(db_router)
app.include_router(auth_router)
app.include_router(vehicle_router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=5000)