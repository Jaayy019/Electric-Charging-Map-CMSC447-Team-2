"""HTTP client helpers for API Ninjas EV endpoints (requires VEHICLE_API_KEY)."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx
from fastapi import HTTPException

BASE_URL = "https://api.api-ninjas.com/v1"


def require_vehicle_api_key() -> str:
    key = (os.getenv("VEHICLE_API_KEY") or "").strip()
    if not key:
        raise HTTPException(
            status_code=503,
            detail=(
                "VEHICLE_API_KEY is not configured. "
                "Set it in `.env` for electric vehicle catalog endpoints."
            ),
        )
    return key


async def ninjas_get_json(path: str, params: Optional[dict[str, Any]] = None) -> Any:
    """GET JSON from API Ninjas with shared timeout and auth headers."""
    api_key = require_vehicle_api_key()
    headers = {"X-Api-Key": api_key}
    url = f"{BASE_URL}/{path.lstrip('/')}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params or {}, headers=headers)
        response.raise_for_status()
        return response.json()
