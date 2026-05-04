"""Database-backed CRUD routes for charge points."""

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from connector_compat import charge_point_compatible_with_vehicle
from database.session import get_session
from database.models import ChargePoint, Connection, Vehicle
from models import ChargePointSummary, ConnectionInfo, LocationInfo

router = APIRouter(prefix="/api/db", tags=["Database"])


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


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points in kilometers."""
    r_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    c = 2 * math.asin(min(1.0, math.sqrt(max(0.0, a))))
    return r_km * c


def _row_operational(cp: ChargePoint) -> bool:
    av = (cp.availability or "").lower()
    if any(x in av for x in ("operational", "available", "open")):
        return True
    return any((c.status or "").lower() == "operational" for c in cp.connections)


async def query_charge_point_summaries(
    session: AsyncSession,
    *,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None,
    port_type: Optional[str] = None,
    vehicle_id: Optional[int] = None,
    vehicle_owner_user_id: Optional[int] = None,
    min_power_kw: Optional[float] = None,
    operational_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[ChargePointSummary]:
    """
    List charge points with optional geo radius, connector / vehicle compatibility,
    power and operational filters. Uses a bounding box in SQL then Haversine in Python.
    """
    if (latitude is None) ^ (longitude is None):
        raise HTTPException(
            status_code=400,
            detail="Provide both latitude and longitude for a location filter, or neither.",
        )

    resolved_vehicle_port: Optional[str] = None
    if vehicle_id is not None:
        vehicle = await session.get(Vehicle, vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        if vehicle_owner_user_id is not None and vehicle.user_id != vehicle_owner_user_id:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        resolved_vehicle_port = vehicle.port_type

    compat_needle = resolved_vehicle_port or port_type

    stmt = select(ChargePoint).options(selectinload(ChargePoint.connections))

    if latitude is not None and longitude is not None:
        rad = radius_km if radius_km is not None else 10.0
        # Rough degrees for bbox prefilter (~ km per degree latitude)
        dlat = rad / 111.0
        cos_lat = math.cos(math.radians(latitude))
        cos_lat = cos_lat if abs(cos_lat) > 1e-6 else 1e-6
        dlng = rad / (111.0 * cos_lat)
        stmt = stmt.where(
            ChargePoint.latitude.between(latitude - dlat, latitude + dlat),
            ChargePoint.longitude.between(longitude - dlng, longitude + dlng),
        )

    result = await session.execute(stmt)
    rows = list(result.scalars().all())

    out_rows: list[ChargePoint] = []
    for cp in rows:
        if operational_only and not _row_operational(cp):
            continue

        if min_power_kw is not None:
            if not any((c.power_kw or 0.0) >= min_power_kw for c in cp.connections):
                continue

        if compat_needle:
            ports = [c.port_type for c in cp.connections]
            if not charge_point_compatible_with_vehicle(compat_needle, ports):
                continue

        if latitude is not None and longitude is not None:
            rad = radius_km if radius_km is not None else 10.0
            dist = _haversine_km(latitude, longitude, cp.latitude, cp.longitude)
            if dist > rad:
                continue

        out_rows.append(cp)

    # Sort by distance when geo context is present
    if latitude is not None and longitude is not None:
        out_rows.sort(key=lambda r: _haversine_km(latitude, longitude, r.latitude, r.longitude))
    else:
        out_rows.sort(key=lambda r: r.id)

    page = out_rows[offset : offset + limit]
    return [charge_point_to_summary(r) for r in page]


# Routes


@router.get("/charge-points", response_model=list[ChargePointSummary])
async def list_charge_points(
    latitude: Optional[float] = Query(None, description="Filter by latitude"),
    longitude: Optional[float] = Query(None, description="Filter by longitude"),
    radius_km: Optional[float] = Query(
        None, description="Search radius in km (default 10 if lat/lng set)"
    ),
    port_type: Optional[str] = Query(
        None, description="Show stations with at least one compatible connector (e.g. CCS)"
    ),
    vehicle_id: Optional[int] = Query(
        None, description="Filter by a saved vehicle's port compatibility (by vehicle id)"
    ),
    min_power_kw: Optional[float] = Query(None, ge=0, description="Minimum connector kW"),
    operational_only: bool = Query(False, description="Only operational stations"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: AsyncSession = Depends(get_session),
):
    """List charge points stored in the database."""
    return await query_charge_point_summaries(
        session,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        port_type=port_type,
        vehicle_id=vehicle_id,
        vehicle_owner_user_id=None,
        min_power_kw=min_power_kw,
        operational_only=operational_only,
        limit=limit,
        offset=offset,
    )


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
