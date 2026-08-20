"""
FleetGuard — Driver Location Tracking Models
Stores GPS positions from driver phones and hardware GPS devices.
Enables live tracking on the dashboard and historical route analysis.
"""

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, Float, String, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.driver_domain import Driver


class LocationSource(str, enum.Enum):
    PHONE_GPS = "PHONE_GPS"
    HARDWARE_GPS = "HARDWARE_GPS"


class AlertType(str, enum.Enum):
    GPS_DRIFT = "GPS_DRIFT"
    SPEED_VIOLATION = "SPEED_VIOLATION"
    GEOFENCE_ENTRY = "GEOFENCE_ENTRY"
    GEOFENCE_EXIT = "GEOFENCE_EXIT"
    SIGNAL_LOST = "SIGNAL_LOST"


class DriverLocation(Base):
    """
    Individual GPS position record from a driver's phone or hardware GPS.
    High-volume table — indexed for time-series queries.
    """
    __tablename__ = "driver_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="Speed in m/s")
    heading: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="Heading in degrees")
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="GPS accuracy in meters")

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        comment="When this position was recorded on the device"
    )

    battery_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    activity_state: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Device activity: DRIVING, WALKING, STATIONARY, etc."
    )

    source: Mapped[LocationSource] = mapped_column(
        Enum(LocationSource, native_enum=False, length=50),
        nullable=False, default=LocationSource.PHONE_GPS,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<DriverLocation(driver={self.driver_id}, lat={self.latitude}, lng={self.longitude})>"


class LocationAlert(Base):
    """
    Alert generated when GPS data indicates anomalies.
    E.g., truck GPS vs phone GPS drift, speed violations, geofence events.
    """
    __tablename__ = "location_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, native_enum=False, length=50),
        nullable=False, index=True,
    )

    details: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    is_resolved: Mapped[bool] = mapped_column(
        default=False, nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<LocationAlert(driver={self.driver_id}, type={self.alert_type.value})>"
