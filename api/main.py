from contextlib import asynccontextmanager
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
from routes import router as db_router

load_dotenv()

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
    lifespan=lifespan,  # lifespan of the app is the lifespan of the engine
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


async def _save_to_local_db(charge_points: List[ChargePointSummary]) -> int:
    """Persist charge points to the local database, skipping duplicates by ID."""
    if engine is None:
        return 0

    saved = 0
    async with async_session_factory() as session:
        for cp in charge_points:
            # Check if this charge point already exists
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
    Fetch charge point data from the external API and return simplified schema.
    Results are automatically saved to the local database for offline access.

    Optionally filter by location using latitude and longitude.

    **Parameters:**
    - `latitude`: Latitude coordinate (e.g., 52.343197)
    - `longitude`: Longitude coordinate (e.g., -0.170632)
    - `distance`: Search radius in kilometers (optional, defaults to 5km)

    Returns only essential information: port types, price, availability, location, etc.
    """

    # Build query parameters for the external API
    params = {"maxresults": 200}

    if latitude is not None and longitude is not None:
        params["latitude"] = latitude
        params["longitude"] = longitude

        # Set distance, default to 5km if not provided
        if distance is not None:
            params["distance"] = distance
        else:
            params["distance"] = 5

        dist = params.get("distance")
        print(f"📍 Location-based search: lat={latitude}, lng={longitude}, distance={dist}km")
    else:
        print("📍 Fetching all charge points (no location filter)")

    result = get_data_from_api(OCM_API_KEY, EXTERNAL_API_URL, USER_AGENT, params)

    if isinstance(result, dict) and "error" in result:
        # External API failed — try serving from local database
        print("External API failed, falling back to local database")
        return await _fallback_from_local_db(latitude, longitude)

    # Transform raw data to simplified schema
    simplified_data, transform_error = transform_to_simplified_schema(result)

    if simplified_data is None:
        return DataResponse(
            status="error",
            data=None,
            total=0,
            error=transform_error or "Failed to transform API data",
        )

    # Save to local database in the background
    try:
        saved_count = await _save_to_local_db(simplified_data)
        if saved_count:
            print(f"Saved {saved_count} new charge points to local database")
    except Exception as e:
        print(f"Failed to save to local database: {e}")

    return DataResponse(
        status="success", data=simplified_data, total=len(simplified_data), error=None
    )


async def _fallback_from_local_db(
    latitude: Optional[float] = None, longitude: Optional[float] = None
) -> DataResponse:
    """Serve cached charge points from the local database when the external API is unavailable."""
    if engine is None:
        return DataResponse(status="error", data=None, total=0, error="No database configured")

    try:
        async with async_session_factory() as session:
            stmt = (
                select(ChargePoint)
                .options(selectinload(ChargePoint.connections))
                .limit(50)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

            if not rows:
                return DataResponse(
                    status="error", data=None, total=0,
                    error="External API unavailable and no cached data found",
                )

            from routes import _row_to_summary
            data = [_row_to_summary(r) for r in rows]
            return DataResponse(
                status="success", data=data, total=len(data), error=None
            )
    except Exception as e:
        return DataResponse(
            status="error", data=None, total=0,
            error=f"External API unavailable and database fallback failed: {e}",
        )


# Mount database-backed routes
app.include_router(db_router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=5000)
