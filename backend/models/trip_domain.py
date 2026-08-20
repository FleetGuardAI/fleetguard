"""
FleetGuard — Trip Domain ORM Models
Represents a trip's identity, status, locations, distance, and time.
"""

from sqlalchemy import Integer, String, Enum, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
import enum
from datetime import datetime

from database import Base

if TYPE_CHECKING:
    from models.vehicle_domain import Vehicle
    from models.driver_domain import Driver
    from models.user import Company


class TripStatus(str, enum.Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # --- Identity & Status ---
    trip_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Business identifier for the trip"
    )
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, native_enum=False, length=50),
        nullable=False, default=TripStatus.CREATED, index=True
    )

    # --- Locations ---
    origin_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    destination_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Distance (in km or standard unit) ---
    planned_distance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_distance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # --- Timing ---
    planned_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Assignments ---
    vehicle_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vehicles.id"), nullable=True, index=True)
    driver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("drivers.id"), nullable=True, index=True)

    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", lazy="selectin")
    driver: Mapped[Optional["Driver"]] = relationship("Driver", lazy="selectin")

    # --- Isolation ---
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id"), nullable=False, index=True, default=1
    )
    company: Mapped[Optional["Company"]] = relationship("Company", lazy="selectin")

    # --- Financial ---
    revenue: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Trip freight/revenue amount in base currency"
    )
    planned_cost: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Estimated/budgeted total cost for this trip"
    )
    planned_fuel_liters: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Planned fuel consumption in liters"
    )
    cargo_weight: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Cargo weight in tonnes"
    )

    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Origin of this state (e.g., 'verified_event')"
    )
    origin_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Reference ID from the origin (e.g., OperationalEvent ID)"
    )

    def __repr__(self) -> str:
        return f"<Trip(id={self.id}, trip_id='{self.trip_id}', status='{self.status.value}')>"
