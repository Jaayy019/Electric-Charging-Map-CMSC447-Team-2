"""Database-backed CRUD routes for charge points."""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.session import get_session
from database.models import ChargePoint, Connection
from models import ChargePointSummary, ConnectionInfo, LocationInfo, AccountCreate, AccountResponse, VehicleCreate, VehicleResponse, Account, Vehicle

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


# Routes


@router.get("/charge-points", response_model=list[ChargePointSummary])
async def list_charge_points(
    latitude: Optional[float] = Query(None, description="Filter by latitude"),
    longitude: Optional[float] = Query(None, description="Filter by longitude"),
    radius_km: Optional[float] = Query(None, description="Search radius in km"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: AsyncSession = Depends(get_session),
):
    """List charge points stored in the database."""
    stmt = (
        select(ChargePoint)
        .options(selectinload(ChargePoint.connections))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
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

@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new user account."""
    stmt = select(Account).where(
        (Account.username == account.username) | (Account.email == account.email)
    )
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )
    
    # TODO: Hash account password/add some security
    new_account = Account(
        username=account.username,
        email=account.email,
        password=account.password,
        created_at=datetime.utcnow(),
    )
    
    session.add(new_account)
    await session.commit()
    await session.refresh(new_account)
    
    return new_account


@router.get("/accounts", response_model=List[AccountResponse])
async def get_accounts(
    session: AsyncSession = Depends(get_session),
):
    """Retrieve all user accounts."""
    stmt = select(Account).options(selectinload(Account.vehicles))
    result = await session.execute(stmt)
    accounts = result.scalars().all()
    return accounts


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve a specific account by ID."""
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account: AccountCreate,
    session: AsyncSession = Depends(get_session),
):
    """Update an existing account."""
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    existing_account = result.scalar_one_or_none()
    
    if existing_account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    existing_account.username = account.username
    existing_account.email = account.email
    # TODO: Hash account password for security
    existing_account.password = account.password
    
    await session.commit()
    await session.refresh(existing_account)
    
    return existing_account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a user account."""
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    await session.delete(account)
    await session.commit()

@router.post("/accounts/{account_id}/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    account_id: int,
    vehicle: VehicleCreate,
    session: AsyncSession = Depends(get_session),
):
    """Add a vehicle to a user account."""
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    new_vehicle = Vehicle(
        account_id=account_id,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        port_type=vehicle.port_type,
        created_at=datetime.utcnow(),
    )
    
    session.add(new_vehicle)
    await session.commit()
    await session.refresh(new_vehicle)
    
    return new_vehicle


@router.get("/accounts/{account_id}/vehicles", response_model=List[VehicleResponse])
async def get_vehicles(
    account_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve all vehicles for a specific account."""
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    stmt = select(Vehicle).where(Vehicle.account_id == account_id)
    result = await session.execute(stmt)
    vehicles = result.scalars().all()
    
    return vehicles


@router.get("/accounts/{account_id}/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    account_id: int,
    vehicle_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve a specific vehicle by ID."""
    stmt = select(Vehicle).where(
        (Vehicle.id == vehicle_id) & (Vehicle.account_id == account_id)
    )
    result = await session.execute(stmt)
    vehicle = result.scalar_one_or_none()
    
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    
    return vehicle


@router.put("/accounts/{account_id}/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    account_id: int,
    vehicle_id: int,
    vehicle: VehicleCreate,
    session: AsyncSession = Depends(get_session),
):
    """Update an existing vehicle."""
    stmt = select(Vehicle).where(
        (Vehicle.id == vehicle_id) & (Vehicle.account_id == account_id)
    )
    result = await session.execute(stmt)
    existing_vehicle = result.scalar_one_or_none()
    
    if existing_vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    
    existing_vehicle.make = vehicle.make
    existing_vehicle.model = vehicle.model
    existing_vehicle.year = vehicle.year
    existing_vehicle.port_type = vehicle.port_type
    
    await session.commit()
    await session.refresh(existing_vehicle)
    
    return existing_vehicle


@router.delete("/accounts/{account_id}/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    account_id: int,
    vehicle_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a vehicle from an account."""
    stmt = select(Vehicle).where(
        (Vehicle.id == vehicle_id) & (Vehicle.account_id == account_id)
    )
    result = await session.execute(stmt)
    vehicle = result.scalar_one_or_none()
    
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    
    await session.delete(vehicle)
    await session.commit()
