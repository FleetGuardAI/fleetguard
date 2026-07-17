"""
FleetGuard — FuelLog ORM Model
Stores raw and filtered fuel level readings from IoT telematics gateways.
"""

from datetime import datetime

from sqlalchemy import Integer, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import TYPE_CHECKING

from database import Base

if TYPE_CHECKING:
    from models.vehicle_domain import Vehicle


class FuelLog(Base):
    __tablename__ = "fuel_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Foreign Key ---
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=False, index=True
    )

    # --- Telemetry Data ---
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        comment="Timestamp of the sensor reading"
    )
    raw_level: Mapped[float] = mapped_column(
        Float, nullable=False,
        comment="Raw fuel level reading in liters (noisy)"
    )
    filtered_level: Mapped[float] = mapped_column(
        Float, nullable=False,
        comment="EMA-smoothed fuel level in liters"
    )
    expected_level: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="Expected fuel level based on distance and consumption rate"
    )
    speed: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="Vehicle speed in km/h at time of reading"
    )

    # --- GPS ---
    latitude: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # --- Alert ---
    is_theft_alert: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True,
        comment="True if this reading triggered a CRITICAL_THEFT alert"
    )

    # --- Meta ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Relationship ---
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="fuel_logs")

    def __repr__(self) -> str:
        return (
            f"<FuelLog(id={self.id}, vehicle={self.vehicle_id}, "
            f"raw={self.raw_level}L, filtered={self.filtered_level}L, "
            f"theft={self.is_theft_alert})>"
        )
