"""
FleetGuard — Emergency Alert Model
SOS alerts triggered by drivers in distress.
"""

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, Float, String, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.driver_domain import Driver


class EmergencyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class EmergencyAlert(Base):
    """
    SOS emergency alert triggered by a driver.
    Immediately notifies fleet manager with live location.
    """
    __tablename__ = "emergency_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    vehicle_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=True,
    )

    trip_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trips.id"), nullable=True,
    )

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[EmergencyStatus] = mapped_column(
        Enum(EmergencyStatus, name="emergency_status"),
        nullable=False, default=EmergencyStatus.ACTIVE, index=True,
    )

    message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    resolved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Relationships ---
    driver: Mapped["Driver"] = relationship("Driver", lazy="selectin")

    def __repr__(self) -> str:
        return f"<EmergencyAlert(id={self.id}, driver_id={self.driver_id}, status={self.status.value})>"
