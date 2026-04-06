"""SQLAlchemy ORM models for charge-point data."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class ChargePoint(Base):
    __tablename__ = "charge_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String, unique=True, index=True)

    # Location
    address: Mapped[str] = mapped_column(String, default="")
    town: Mapped[str] = mapped_column(String, default="")
    postcode: Mapped[str] = mapped_column(String, default="")
    country: Mapped[str] = mapped_column(String, default="")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    contact_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Details
    number_of_points: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    availability: Mapped[str] = mapped_column(String, default="Unknown")
    membership_required: Mapped[bool] = mapped_column(Boolean, default=False)
    access_key_required: Mapped[bool] = mapped_column(Boolean, default=False)
    operator: Mapped[str] = mapped_column(String, default="Unknown")
    last_verified: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    connections: Mapped[List[Connection]] = relationship(
        back_populates="charge_point", cascade="all, delete-orphan"
    )


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    charge_point_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("charge_points.id", ondelete="CASCADE")
    )

    port_type: Mapped[str] = mapped_column(String, default="Unknown")
    power_kw: Mapped[float] = mapped_column(Float, default=0.0)
    voltage: Mapped[int] = mapped_column(Integer, default=0)
    amps: Mapped[int] = mapped_column(Integer, default=0)
    current_type: Mapped[str] = mapped_column(String, default="Unknown")
    status: Mapped[str] = mapped_column(String, default="Unknown")
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    charge_point: Mapped[ChargePoint] = relationship(back_populates="connections")
