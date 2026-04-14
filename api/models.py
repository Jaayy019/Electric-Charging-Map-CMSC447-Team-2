from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr

Base = declarative_base()

class ConnectionInfo(BaseModel):
    """Simplified connection/port information."""

    id: int
    port_type: str  # e.g., "Type 2 (Socket Only)"
    power_kw: float  # e.g., 7.4
    voltage: int  # e.g., 230
    amps: int  # e.g., 32
    current_type: str  # e.g., "AC (Single-Phase)"
    status: str  # e.g., "Operational"
    quantity: int  # Number of this type of port


class LocationInfo(BaseModel):
    """Simplified location information."""

    address: str
    town: str
    postcode: str
    country: str
    latitude: float
    longitude: float
    contact_email: Optional[str] = None


class ChargePointSummary(BaseModel):
    """Simplified charge point data."""

    id: int
    uuid: str
    location: LocationInfo
    connections: List[ConnectionInfo]
    number_of_points: int
    price: Optional[str] = None  # Usage cost
    availability: str  # Status (e.g., "Operational")
    membership_required: bool
    access_key_required: bool
    operator: str
    last_verified: Optional[datetime] = None


class ChargePointsResponse(BaseModel):
    """Response containing multiple charge points."""

    charge_points: List[ChargePointSummary]
    total: int


class VehicleCreate(BaseModel):
    """Request body for adding a vehicle to a user account."""

    make: str
    model: str
    year: int
    port_type: str


class VehicleResponse(BaseModel):
    """Response for a saved vehicle."""

    id: int
    make: str
    model: str
    year: int
    port_type: str
    created_at: datetime


class AccountCreate(BaseModel):
    """Request body for creating a new user account."""

    username: str
    email: str
    password: str


class AccountResponse(BaseModel):
    """Response after successful account creation."""

    id: int
    username: str
    email: str
    created_at: datetime

class Account(Base):
    """User account model."""
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    vehicles: Mapped[List["Vehicle"]] = relationship(
        "Vehicle",
        back_populates="account",
        cascade="all, delete-orphan"
    )


class Vehicle(Base):
    """Vehicle model associated with an account."""
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    port_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="vehicles"
    )
