"""Database-backed CRUD routes for charge points."""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import ChargePoint, Connection
from database.session import get_session
from models import ChargePointSummary, ConnectionInfo, LocationInfo

router = APIRouter(prefix="/api/db", tags=["Database"])


# Geo helpers
_EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the circle distance in kilometres between two lat/lng points."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return _EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def _bounding_box(
    latitude: float, longitude: float, radius_km: float
) -> tuple[float, float, float, float]:
    """Return (min_lat, max_lat, min_lon, max_lon) for a rough bounding box.

    latitude = 111.32 km (constant) due to dividing the Earth's circumference by 360.
    longitude = 111.32 * cos(lat) km (shrinks toward the poles).
    """
    lat_delta = radius_km / 111.32
    lon_delta = radius_km / (111.32 * max(math.cos(math.radians(latitude)), 1e-9))
    return (
        latitude - lat_delta,
        latitude + lat_delta,
        longitude - lon_delta,
        longitude + lon_delta,
    )


# Helpers — convert between ORM rows and Pydantic response models


def charge_point_to_summary(row: ChargePoint) -> ChargePointSummary:
    """Convert a ChargePoint ORM object to a Pydantic ChargePointSummary."""
    return ChargePointSummary(
        id=row.id,
        uuid=row.uuid,
        location=LocationInfo(
            address=row.address,
            town=row.town,
            postcode=row.postcode,
            country=row.country,
            latitude=row.latitude,
            longitude=row.longitude,
            contact_email=row.contact_email,
        ),
        connections=[
            ConnectionInfo(
                id=c.id,
                port_type=c.port_type,
                power_kw=c.power_kw,
                voltage=c.voltage,
                amps=c.amps,
                current_type=c.current_type,
                status=c.status,
                quantity=c.quantity,
            )
            for c in row.connections
        ],
        number_of_points=row.number_of_points,
        price=row.price,
        availability=row.availability,
        membership_required=row.membership_required,
        access_key_required=row.access_key_required,
        operator=row.operator,
        last_verified=row.last_verified,
    )


def _summary_to_row(data: ChargePointSummary) -> ChargePoint:
    """Convert a Pydantic ChargePointSummary into an ORM ChargePoint."""
    row = ChargePoint(
        id=data.id,
        uuid=data.uuid,
        address=data.location.address,
        town=data.location.town,
        postcode=data.location.postcode,
        country=data.location.country,
        latitude=data.location.latitude,
        longitude=data.location.longitude,
        contact_email=data.location.contact_email,
        number_of_points=data.number_of_points,
        price=data.price,
        availability=data.availability,
        membership_required=data.membership_required,
        access_key_required=data.access_key_required,
        operator=data.operator,
        last_verified=data.last_verified,
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
            for c in data.connections
        ],
    )
    return row


# Routes


@router.get("/charge-points", response_model=list[ChargePointSummary])
async def list_charge_points(
    latitude: Optional[float] = Query(None, description="Filter by latitude"),
    longitude: Optional[float] = Query(None, description="Filter by longitude"),
    radius_km: Optional[float] = Query(
        None, description="Search radius in km (requires latitude and longitude)"
    ),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: AsyncSession = Depends(get_session),
):
    """List charge points stored in the database.

    When latitude, longitude, and radius_km are all given the results
    are filtered to a circle of the given radius using a two pass strategy:

    1. Bounding box SQL filter — a BETWEEN pre filter that works on
       SQLite (tests)/Postgres (production).
    2. Haversine post filter — an exact circle check in Python that removes
       the corners of the bounding box, which are further away than the radius.
    """
    #Check if all geo parameters are provided
    geo_filter = latitude is not None and longitude is not None and radius_km is not None
    #Create a select statement with loading for connections
    stmt = select(ChargePoint).options(selectinload(ChargePoint.connections))

    #If geo parameters are provided, filter by bounding box
    if geo_filter:
        min_lat, max_lat, min_lon, max_lon = _bounding_box(latitude, longitude, radius_km)
        stmt = stmt.where(
            ChargePoint.latitude.between(min_lat, max_lat),
            ChargePoint.longitude.between(min_lon, max_lon),
        )

        #Fetch everything inside the bounding box, Haversine will trim the corners.
        #Skip SQL LIMIT/OFFSET here so pagination applies to the precise result set.
        result = await session.execute(stmt)
        all_rows = result.scalars().all()

        rows_in_circle = [
            r
            for r in all_rows
            if _haversine_km(latitude, longitude, r.latitude, r.longitude) <= radius_km
        ]
        #Apply offset + limit after the precise filter
        rows = rows_in_circle[offset : offset + limit]
    else:
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = list(result.scalars().all())

    return [charge_point_to_summary(r) for r in rows]


@router.get("/charge-points/{charge_point_id}", response_model=ChargePointSummary)
async def get_charge_point(
    charge_point_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a single charge point by ID."""
    stmt = (
        select(ChargePoint)
        .options(selectinload(ChargePoint.connections))
        .where(ChargePoint.id == charge_point_id)
    )
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Charge point not found")
    return charge_point_to_summary(row)


@router.post("/charge-points", response_model=ChargePointSummary, status_code=201)
async def create_charge_point(
    data: ChargePointSummary,
    session: AsyncSession = Depends(get_session),
):
    """Save a charge point to the database."""
    row = _summary_to_row(data)
    session.add(row)
    await session.commit()
    await session.refresh(row, attribute_names=["connections"])
    return charge_point_to_summary(row)


@router.post("/charge-points/bulk", response_model=dict, status_code=201)
async def bulk_create_charge_points(
    data: list[ChargePointSummary],
    session: AsyncSession = Depends(get_session),
):
    """Save multiple charge points to the database at once."""
    rows = [_summary_to_row(d) for d in data]
    session.add_all(rows)
    await session.commit()
    return {"saved": len(rows)}


@router.delete("/charge-points/{charge_point_id}", status_code=204)
async def delete_charge_point(
    charge_point_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a charge point by ID."""
    stmt = select(ChargePoint).where(ChargePoint.id == charge_point_id)
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Charge point not found")
    await session.delete(row)
    await session.commit()
