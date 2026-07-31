"""
FleetGuard — Vehicle Inspection Model
Pre-trip and post-trip inspection records with checklist items and photos.
"""

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.driver_domain import Driver
    from models.vehicle_domain import Vehicle


class InspectionType(str, enum.Enum):
    PRE_TRIP = "PRE_TRIP"
    POST_TRIP = "POST_TRIP"


class InspectionStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"


class VehicleInspection(Base):
    """
    Vehicle inspection report created by drivers before or after trips.
    Failed items automatically generate maintenance tickets.
    """
    __tablename__ = "vehicle_inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    inspection_type: Mapped[InspectionType] = mapped_column(
        Enum(InspectionType, name="inspection_type"),
        nullable=False, index=True,
    )

    overall_status: Mapped[InspectionStatus] = mapped_column(
        Enum(InspectionStatus, name="inspection_status"),
        nullable=False, default=InspectionStatus.PASS,
    )

    items: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
        comment="Checklist items: {item_name: {status, notes, photo_url}}"
    )

    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # --- Relationships ---
    driver: Mapped["Driver"] = relationship("Driver", lazy="selectin")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", lazy="selectin")

    def __repr__(self) -> str:
        return f"<VehicleInspection(id={self.id}, type={self.inspection_type.value}, status={self.overall_status.value})>"
