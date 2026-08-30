"""
FleetGuard — Driver Domain ORM Models
Represents a driver's identity and employment status in the fleet.
Extended with mobile app fields for onboarding, documents, and live tracking.
"""

from sqlalchemy import Integer, String, Float, Enum, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
import enum
from datetime import date, datetime

from database import Base

if TYPE_CHECKING:
    from models.ticket import Ticket
    from models.company import Company
    from models.user import User


class DriverStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class EmploymentStatus(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    CONTRACT = "CONTRACT"
    TEMPORARY = "TEMPORARY"


class VerificationStatus(str, enum.Enum):
    PENDING_DOCUMENTS = "PENDING_DOCUMENTS"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DutyStatus(str, enum.Enum):
    OFF_DUTY = "OFF_DUTY"
    ON_DUTY = "ON_DUTY"
    ON_BREAK = "ON_BREAK"


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
        comment="WhatsApp phone number in E.164 format (e.g. +919876543210)"
    )
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # --- Multi-Tenancy (added for driver app) ---
    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True, index=True,
        comment="The fleet company this driver belongs to"
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, unique=True,
        comment="Linked user account for authentication"
    )

    # --- Identity & License ---
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    license_valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # --- Document URLs (added for driver app) ---
    license_front_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    license_back_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    aadhaar_front_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    aadhaar_back_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    selfie_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    aadhaar_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # --- Verification (added for driver app) ---
    verification_status: Mapped[Optional[VerificationStatus]] = mapped_column(
        Enum(VerificationStatus, native_enum=False, length=50),
        nullable=True, default=None, index=True,
        comment="Mobile app onboarding verification status"
    )
    face_verified: Mapped[Optional[bool]] = mapped_column(default=None, nullable=True)

    # --- Business Status ---
    employment_status: Mapped[Optional[EmploymentStatus]] = mapped_column(
        Enum(EmploymentStatus, native_enum=False, length=50),
        nullable=True
    )
    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus, native_enum=False, length=50),
        nullable=False, default=DriverStatus.ACTIVE, index=True
    )

    # --- Duty Status (added for driver app) ---
    duty_status: Mapped[Optional[DutyStatus]] = mapped_column(
        Enum(DutyStatus, native_enum=False, length=50),
        nullable=True, default=None,
        comment="Current duty status from the mobile app"
    )

    # --- Live Location (added for driver app) ---
    last_known_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_known_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_location_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- FCM (added for driver app) ---
    fcm_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # --- Driver Score ---
    driver_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=85.0)

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
    company: Mapped[Optional["Company"]] = relationship("Company", lazy="selectin")
    user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="driver")

    def __repr__(self) -> str:
        return f"<Driver(id={self.id}, name='{self.name}', status='{self.status.value}')>"
