"""
FleetGuard — Driver Qualification Model
Captures structured qualifications, driving license classes, endorsements,
certifications, validity dates, and authorized verification status.
"""

import enum
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, String, Date, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.driver_domain import Driver
    from models.user import Company


class QualificationType(str, enum.Enum):
    DRIVING_LICENSE = "DRIVING_LICENSE"
    HAZMAT_CERTIFICATION = "HAZMAT_CERTIFICATION"
    HEAVY_VEHICLE_ENDORSEMENT = "HEAVY_VEHICLE_ENDORSEMENT"
    TANKER_ENDORSEMENT = "TANKER_ENDORSEMENT"
    PERISHABLE_CARGO_HANDLING = "PERISHABLE_CARGO_HANDLING"
    FIRST_AID_SAFETY = "FIRST_AID_SAFETY"


class LicenseClass(str, enum.Enum):
    LMV = "LMV"          # Light Motor Vehicle
    MGV = "MGV"          # Medium Goods Vehicle
    HGV = "HGV"          # Heavy Goods Vehicle
    HMV = "HMV"          # Heavy Motor Vehicle
    HAZMAT = "HAZMAT"    # Hazardous Materials Endorsement
    TANKER = "TANKER"    # Bulk Liquid/Gas Tanker


class QualificationVerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class DriverQualification(Base):
    __tablename__ = "driver_qualifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    qualification_type: Mapped[QualificationType] = mapped_column(
        Enum(QualificationType, native_enum=False, length=50),
        nullable=False,
        default=QualificationType.DRIVING_LICENSE,
        index=True
    )

    license_class: Mapped[Optional[LicenseClass]] = mapped_column(
        Enum(LicenseClass, native_enum=False, length=50),
        nullable=True,
        index=True,
        comment="Specific license class (LMV, MGV, HGV, HMV, HAZMAT, TANKER)"
    )

    certificate_number: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Unique identifier of the license or certificate"
    )

    issuing_authority: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True,
        comment="Authority or jurisdiction that issued the credential (e.g. RTO MH-12, DOT)"
    )

    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)

    verification_status: Mapped[QualificationVerificationStatus] = mapped_column(
        Enum(QualificationVerificationStatus, native_enum=False, length=50),
        nullable=False,
        default=QualificationVerificationStatus.PENDING,
        index=True
    )

    verified_by: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Identifier/email of the authorized admin/reviewer who verified the qualification"
    )

    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    evidence_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="Reference or URL to supporting document/evidence"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    driver: Mapped["Driver"] = relationship("Driver", back_populates="qualifications", lazy="selectin")
    company: Mapped["Company"] = relationship("Company", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DriverQualification(id={self.id}, driver_id={self.driver_id}, type={self.qualification_type.value}, status={self.verification_status.value})>"
