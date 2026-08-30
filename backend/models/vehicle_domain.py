"""
FleetGuard — Vehicle Domain ORM Models
Represents a vehicle and its state in the fleet.
"""

from sqlalchemy import Integer, String, Float, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
import enum

from database import Base

if TYPE_CHECKING:
    from models.ticket import Ticket
    from models.fuel_log import FuelLog
    from models.user import Company
    from models.driver_domain import Driver


class VehicleStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registration_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
        comment="Vehicle license plate / registration"
    )
    vin: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True, index=True,
        comment="Vehicle Identification Number / Chassis Number"
    )
    engine_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Engine Number"
    )
    
    # --- Specifications ---
    make: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tank_capacity: Mapped[float] = mapped_column(
        Float, nullable=False, default=400.0,
        comment="Fuel tank capacity in liters"
    )
    
    # --- Business Status ---
    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, native_enum=False, length=50),
        nullable=False, default=VehicleStatus.ACTIVE, index=True
    )
    ownership_info: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Details about ownership (Leased, Owned, etc.)"
    )
    
    # --- Traceability ---
    origin_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Origin of this state (e.g., 'verified_event', 'system')"
    )
    origin_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Reference ID from the origin (e.g., OperationalEvent ID)"
    )

    # --- Isolation ---
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id"), nullable=False, index=True, default=1
    )
    company: Mapped["Company"] = relationship("Company", lazy="selectin")

    # --- Driver Assignment ---
    assigned_driver_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="Currently assigned driver"
    )
    assigned_driver: Mapped[Optional["Driver"]] = relationship("Driver", lazy="selectin", foreign_keys=[assigned_driver_id])

    # --- Relationships ---
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="vehicle", lazy="selectin"
    )
    fuel_logs: Mapped[list["FuelLog"]] = relationship(
        "FuelLog", back_populates="vehicle", lazy="selectin"
    )
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="vehicle")

    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, reg='{self.registration_number}', make='{self.make}')>"
