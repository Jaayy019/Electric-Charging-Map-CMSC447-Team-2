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
from database import dispose_engine, engine
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

    Optionally filter by location using latitude and longitude.

    **Parameters:**
    - `latitude`: Latitude coordinate (e.g., 52.343197)
    - `longitude`: Longitude coordinate (e.g., -0.170632)
    - `distance`: Search radius in kilometers (optional, defaults to 5km)

    Returns only essential information: port types, price, availability, location, etc.
    """

    # Build query parameters for the external API
    params = {}

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
        return DataResponse(status="error", data=None, total=0, error=result["error"])

    # Transform raw data to simplified schema
    simplified_data, transform_error = transform_to_simplified_schema(result)

    if simplified_data is None:
        return DataResponse(
            status="error",
            data=None,
            total=0,
            error=transform_error or "Failed to transform API data",
        )

    return DataResponse(
        status="success", data=simplified_data, total=len(simplified_data), error=None
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
