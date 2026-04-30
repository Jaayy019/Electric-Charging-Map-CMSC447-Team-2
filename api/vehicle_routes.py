import urllib.request
import json
import httpx
import os

from fastapi import APIRouter, Query

API_KEY = os.getenv("VEHICLE_API_KEY")

router = APIRouter(prefix="/api/vehicle", tags=["Vehicle"])

@router.get("/makes")
def get_all_makes():
    """
    Fetches all vehicle makes from the NHTSA API
    """
    url = "https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
    return data

@router.get("/vehicles/models/{manufacturer}")
async def get_models_for_make(manufacturer: str):
    """
    Fetches all vehicle models for a given manufacturer from the NHTSA API
    
    Args:
        manufacturer: The manufacturer name (e.g., 'Toyota', 'Ford', 'BMW')
    """
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{manufacturer}?format=json"
    
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
    
    headers = {
        "X-Api-Key": API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.api-ninjas.com/v1/electricvehicle",
            params=params,
            headers=headers
        )
        response.raise_for_status()
        return response.json()