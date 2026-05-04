import os
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

API_KEY = os.getenv("VEHICLE_API_KEY")

router = APIRouter(prefix="/api/vehicle", tags=["Vehicle"])


# Curated list of major consumer auto manufacturers. NHTSA's getallmakes returns
# thousands of LLCs / commercial-only brands, so we expose this set instead.
MANUFACTURERS: list[str] = [
    "Acura",
    "Audi",
    "BMW",
    "Buick",
    "Cadillac",
    "Chevrolet",
    "Chrysler",
    "Dodge",
    "Ford",
    "Genesis",
    "GMC",
    "Honda",
    "Hyundai",
    "Infiniti",
    "Jaguar",
    "Jeep",
    "Kia",
    "Land Rover",
    "Lexus",
    "Lincoln",
    "Lucid",
    "Mazda",
    "Mercedes-Benz",
    "Mini",
    "Mitsubishi",
    "Nissan",
    "Polestar",
    "Porsche",
    "Ram",
    "Rivian",
    "Subaru",
    "Tesla",
    "Toyota",
    "Volkswagen",
    "Volvo",
]

_MANUFACTURER_LOOKUP = {m.casefold(): m for m in MANUFACTURERS}


def canonical_manufacturer(make: str) -> Optional[str]:
    """Return the canonical-cased manufacturer name, or None if not in the curated list."""
    if not make:
        return None
    return _MANUFACTURER_LOOKUP.get(make.strip().casefold())


async def fetch_models_for_make(manufacturer: str) -> list[str]:
    """Fetch model names for a manufacturer from NHTSA. Returns [] on network failure."""
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{manufacturer}?format=json"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return []
    return [r.get("Model_Name", "") for r in data.get("Results", []) if r.get("Model_Name")]


async def is_valid_model(manufacturer: str, model: str) -> Optional[bool]:
    """
    True if NHTSA lists `model` under `manufacturer`, False if it returned a list that
    doesn't include the model, None if NHTSA was unreachable (caller should pass through).
    """
    if not model:
        return False
    models = await fetch_models_for_make(manufacturer)
    if not models:
        return None
    target = model.strip().casefold()
    return any(m.casefold() == target for m in models)


@router.get("/manufacturers")
def get_manufacturers() -> dict[str, list[str]]:
    """Curated list of major consumer auto manufacturers."""
    return {"manufacturers": MANUFACTURERS}


@router.get("/vehicles/models/{manufacturer}")
async def get_models_for_make(manufacturer: str):
    """
    Fetches all vehicle models for a given manufacturer from the NHTSA API.

    The manufacturer must be one of the curated brands from `/api/vehicle/manufacturers`.
    """
    canonical = canonical_manufacturer(manufacturer)
    if canonical is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown manufacturer '{manufacturer}'. See /api/vehicle/manufacturers.",
        )

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{canonical}?format=json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


@router.get("/electric-vehicles")
async def get_electric_vehicles(
    make: str = Query(None, description="Vehicle manufacturer (e.g. tesla or nissan)"),
    model: str = Query(None, description="Vehicle model (supports partial matching)"),
    min_year: int = Query(None, description="Minimum vehicle model year"),
    max_year: int = Query(None, description="Maximum vehicle model year"),
    min_range: int = Query(None, description="Minimum range in kilometers"),
    max_range: int = Query(None, description="Maximum range in kilometers"),
):
    """
    Fetches electric vehicles from the API Ninjas Electric Vehicle API

    All parameters are optional. You can filter by make, model, year range, or range.
    """

    # Build query parameters, only including non-None values
    params = {}
    if make:
        params["make"] = make
    if model:
        params["model"] = model
    if min_year:
        params["min_year"] = min_year
    if max_year:
        params["max_year"] = max_year
    if min_range:
        params["min_range"] = min_range
    if max_range:
        params["max_range"] = max_range

    headers = {"X-Api-Key": API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.api-ninjas.com/v1/electricvehicle", params=params, headers=headers
        )
        response.raise_for_status()
        return response.json()
