"""External EV catalog (NHTSA + API Ninjas). Requires VEHICLE_API_KEY for EV endpoints."""

from __future__ import annotations

import json
import urllib.request
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Query

from api_ninjas_vehicle import ninjas_get_json, require_vehicle_api_key

load_dotenv()

router = APIRouter(prefix="/api/vehicle", tags=["Vehicle"])


@router.get("/makes")
def get_all_makes():
    """
    Fetches all vehicle makes from the NHTSA API.
    """
    url = "https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
    return data


@router.get("/vehicles/models/{manufacturer}")
async def get_models_for_make(manufacturer: str):
    """
    Fetches all vehicle models for a given manufacturer from the NHTSA API.
    """
    url = (
        f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake"
        f"/{manufacturer}?format=json"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


@router.get("/electric-makes")
async def get_electric_makes():
    """
    All electric vehicle manufacturers from API Ninjas.
    Requires VEHICLE_API_KEY to be set.
    """
    return await ninjas_get_json("electricvehiclemakes")


@router.get("/electric-vehicles")
async def get_electric_vehicles(
    make: Optional[str] = Query(None, description="Vehicle manufacturer (e.g. tesla)"),
    model: Optional[str] = Query(None, description="Vehicle model (partial match)"),
    min_year: Optional[int] = Query(None, description="Minimum vehicle model year"),
    max_year: Optional[int] = Query(None, description="Maximum vehicle model year"),
    min_range: Optional[int] = Query(None, description="Minimum range in kilometers"),
    max_range: Optional[int] = Query(None, description="Maximum range in kilometers"),
):
    """
    Electric vehicle specs from API Ninjas.
    At least one filter parameter is required.
    """
    require_vehicle_api_key()

    params: dict = {}
    if make:
        params["make"] = make
    if model:
        params["model"] = model
    if min_year is not None:
        params["min_year"] = min_year
    if max_year is not None:
        params["max_year"] = max_year
    if min_range is not None:
        params["min_range"] = min_range
    if max_range is not None:
        params["max_range"] = max_range

    if not params:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=(
                "Provide at least one filter: make, model, min_year, max_year, "
                "min_range, or max_range."
            ),
        )

    return await ninjas_get_json("electricvehicle", params)