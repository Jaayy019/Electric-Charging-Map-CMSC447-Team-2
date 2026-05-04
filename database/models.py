"""SQLAlchemy ORM models for charge-point and user data."""

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


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sessions: Mapped[List[Session]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    vehicles: Mapped[List[Vehicle]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    user: Mapped[User] = relationship(back_populates="sessions")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    make: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)
    port_type: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="vehicles")


class ChargePoint(Base):
    __tablename__ = "charge_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String, unique=True, index=True)

    address: Mapped[str] = mapped_column(String, default="")
    town: Mapped[str] = mapped_column(String, default="")
    postcode: Mapped[str] = mapped_column(String, default="")
    country: Mapped[str] = mapped_column(String, default="")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    contact_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    number_of_points: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    availability: Mapped[str] = mapped_column(String, default="Unknown")
    membership_required: Mapped[bool] = mapped_column(Boolean, default=False)
    access_key_required: Mapped[bool] = mapped_column(Boolean, default=False)
    operator: Mapped[str] = mapped_column(String, default="Unknown")
    last_verified: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

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

    charge_point: Mapped[ChargePoint] = relationship(back_populates="connections")
