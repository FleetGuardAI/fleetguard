"""
FleetGuard — Driver Domain ORM Models
Represents a driver's identity and employment status in the fleet.
"""

from sqlalchemy import Integer, String, Enum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
import enum
from datetime import date

from database import Base

if TYPE_CHECKING:
    from models.ticket import Ticket


class DriverStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class EmploymentStatus(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    CONTRACT = "CONTRACT"
    TEMPORARY = "TEMPORARY"


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
        comment="WhatsApp phone number in E.164 format (e.g. +919876543210)"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # --- Identity & License ---
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    license_valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # --- Business Status ---
    employment_status: Mapped[Optional[EmploymentStatus]] = mapped_column(
        Enum(EmploymentStatus, name="driver_employment_status"),
        nullable=True
    )
    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus, name="driver_status"),
        nullable=False, default=DriverStatus.ACTIVE, index=True
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

    # --- Relationships ---
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="driver", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Driver(id={self.id}, name='{self.name}', status='{self.status.value}')>"
