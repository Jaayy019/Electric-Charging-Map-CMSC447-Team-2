"""External EV catalog (API Ninjas). Requires VEHICLE_API_KEY."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api_ninjas_vehicle import ninjas_get_json, require_vehicle_api_key

router = APIRouter(prefix="/api/vehicle", tags=["Vehicle"])


@router.get("/electric-makes")
async def get_electric_makes():
    """All electric vehicle manufacturers (API Ninjas)."""
    return await ninjas_get_json("electricvehiclemakes")


@router.get("/electric-models")
async def get_electric_models(
    make: str = Query(..., description="Manufacturer slug or name (e.g. tesla)"),
    year: Optional[int] = Query(None, description="Optional model year filter"),
):
    """Electric vehicle models for a make (API Ninjas)."""
    params: dict = {"make": make}
    if year is not None:
        params["year"] = year
    return await ninjas_get_json("electricvehiclemodels", params)


@router.get("/makes")
async def get_all_makes_alias():
    """Alias for `/electric-makes` (EV-only; replaces legacy NHTSA list)."""
    return await get_electric_makes()


@router.get("/vehicles/models/{manufacturer}")
async def get_models_for_make_alias(manufacturer: str):
    """Alias for `/electric-models?make={manufacturer}` (EV-only)."""
    return await get_electric_models(make=manufacturer)


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

    API Ninjas requires at least one filter besides pagination — we mirror that rule.
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
        raise HTTPException(
            status_code=400,
            detail=(
                "Provide at least one filter: make, model, min_year, max_year, "
                "min_range, or max_range."
            ),
        )

    return await ninjas_get_json("electricvehicle", params)
