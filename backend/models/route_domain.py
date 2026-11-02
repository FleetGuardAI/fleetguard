"""
FleetGuard — Route Optimization, Versioning & Deviation ORM Models
Defines persistent route versions, cost estimates, and deviation incidents.
"""

import enum
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, String, Float, Text, Enum, DateTime, ForeignKey, func, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.trip_domain import Trip
    from models.company import Company
    from models.driver_domain import Driver
    from models.vehicle_domain import Vehicle
    from models.user import User


class RouteType(str, enum.Enum):
    RECOMMENDED = "RECOMMENDED"
    FASTEST = "FASTEST"
    LOWEST_COST = "LOWEST_COST"
    ALTERNATIVE = "ALTERNATIVE"
    RECALCULATED = "RECALCULATED"


class RouteVersionStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"


class DeviationStatus(str, enum.Enum):
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"
    OBSTRUCTION_REPORTED = "OBSTRUCTION_REPORTED"
    APPROVED_DETOUR = "APPROVED_DETOUR"
    RETURNED_TO_ROUTE = "RETURNED_TO_ROUTE"
    RESOLVED = "RESOLVED"


class DeviationSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ObstructionReason(str, enum.Enum):
    ROAD_CLOSED = "ROAD_CLOSED"
    TRAFFIC_DIVERSION = "TRAFFIC_DIVERSION"
    VEHICLE_BREAKDOWN = "VEHICLE_BREAKDOWN"
    ACCIDENT = "ACCIDENT"
    WEATHER = "WEATHER"
    SAFETY_CONCERN = "SAFETY_CONCERN"
    CLIENT_INSTRUCTION = "CLIENT_INSTRUCTION"
    OTHER = "OTHER"


class RouteVersion(Base):
    """
    Persisted route plan with complete geometry, cost breakdown, and versioning.
    Allows auditability of changes throughout a trip's lifecycle.
    """
    __tablename__ = "route_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    route_type: Mapped[RouteType] = mapped_column(
        Enum(RouteType, native_enum=False, length=50),
        nullable=False,
        default=RouteType.RECOMMENDED
    )

    status: Mapped[RouteVersionStatus] = mapped_column(
        Enum(RouteVersionStatus, native_enum=False, length=50),
        nullable=False,
        default=RouteVersionStatus.PLANNED,
        index=True
    )

    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lng: Mapped[float] = mapped_column(Float, nullable=False)
    origin_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    destination_lat: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lng: Mapped[float] = mapped_column(Float, nullable=False)
    destination_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    polyline: Mapped[str] = mapped_column(Text, nullable=False, comment="Encoded Google/OSRM polyline")
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Cost Estimation
    fuel_liters_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fuel_cost_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    toll_cost_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_cost_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")

    vehicle_mileage_used: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fuel_price_used: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    routing_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="google")

    selection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reason_for_change: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    approved_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    trip: Mapped[Optional["Trip"]] = relationship("Trip", foreign_keys=[trip_id], back_populates="route_versions")
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_user_id])

    def __repr__(self) -> str:
        return f"<RouteVersion(id={self.id}, trip_id={self.trip_id}, v={self.version_number}, status={self.status.value})>"


class RouteDeviationEvent(Base):
    """
    Authoritative record of a confirmed or reported route deviation incident.
    Tracks state progression, distance, driver explanations, and management resolution.
    """
    __tablename__ = "route_deviation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    event_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False,
        comment="Business identifier for the deviation incident (e.g. DEV-8A1B2C3D)"
    )

    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    driver_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    vehicle_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    route_version_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("route_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[DeviationStatus] = mapped_column(
        Enum(DeviationStatus, native_enum=False, length=50),
        nullable=False,
        default=DeviationStatus.SUSPECTED,
        index=True
    )

    severity: Mapped[DeviationSeverity] = mapped_column(
        Enum(DeviationSeverity, native_enum=False, length=20),
        nullable=False,
        default=DeviationSeverity.MEDIUM
    )

    distance_from_route_meters: Mapped[float] = mapped_column(Float, nullable=False)
    max_distance_meters: Mapped[float] = mapped_column(Float, nullable=False)

    last_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    last_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    gps_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    consecutive_outliers: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Driver Reporting
    driver_explanation_category: Mapped[Optional[ObstructionReason]] = mapped_column(
        Enum(ObstructionReason, native_enum=False, length=50), nullable=True
    )
    driver_explanation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    driver_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Fleet Management Actions
    manager_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    acknowledged_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    trip: Mapped[Optional["Trip"]] = relationship("Trip", foreign_keys=[trip_id], back_populates="deviation_events")
    driver: Mapped[Optional["Driver"]] = relationship("Driver", foreign_keys=[driver_id])
    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", foreign_keys=[vehicle_id])
    route_version: Mapped[Optional["RouteVersion"]] = relationship("RouteVersion", foreign_keys=[route_version_id])
    acknowledged_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[acknowledged_by_user_id])

    def __repr__(self) -> str:
        return f"<RouteDeviationEvent(id={self.id}, event_id='{self.event_id}', status={self.status.value}, dist={self.distance_from_route_meters:.1f}m)>"
