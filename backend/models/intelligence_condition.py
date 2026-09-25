"""
FleetGuard — Driver Vehicle Intelligence Condition Model

Tracks the persistent state of anomaly conditions over time.
Ensures we don't spam alerts for every location update, but rather track duration.
"""

from typing import Optional, TYPE_CHECKING
import enum
from datetime import datetime

from sqlalchemy import Integer, String, Enum, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base

if TYPE_CHECKING:
    from models.vehicle_domain import Vehicle
    from models.driver_domain import Driver
    from models.trip_domain import Trip
    from models.location_tracking import LocationAlert


class ConditionType(str, enum.Enum):
    POTENTIAL_DRIVER_VEHICLE_SEPARATION = "POTENTIAL_DRIVER_VEHICLE_SEPARATION"
    VEHICLE_MOVING_DRIVER_STATIONARY = "VEHICLE_MOVING_DRIVER_STATIONARY"
    GPS_SOURCE_DIVERGENCE = "GPS_SOURCE_DIVERGENCE"


class ConditionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class IntelligenceCondition(Base):
    __tablename__ = "intelligence_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    driver_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trip_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True
    )

    condition_type: Mapped[ConditionType] = mapped_column(
        Enum(ConditionType, native_enum=False, length=100), nullable=False
    )
    
    status: Mapped[ConditionStatus] = mapped_column(
        Enum(ConditionStatus, native_enum=False, length=50), nullable=False, default=ConditionStatus.ACTIVE, index=True
    )

    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    last_evidence: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    alert_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("location_alerts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # Ensure only one active condition of a given type per vehicle
        Index(
            "uq_active_condition_per_vehicle",
            "company_id", "vehicle_id", "condition_type",
            unique=True,
            postgresql_where=status == "ACTIVE"
        ),
    )

    def __repr__(self):
        return f"<IntelligenceCondition(vehicle_id={self.vehicle_id}, type={self.condition_type.value}, status={self.status.value})>"
