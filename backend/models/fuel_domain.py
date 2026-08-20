"""
FleetGuard — Fuel Domain ORM Models
Represents the business state and history of fuel in the fleet.
"""

from datetime import datetime
import enum

from sqlalchemy import Integer, Float, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, Optional

from database import Base

if TYPE_CHECKING:
    from models.vehicle_domain import Vehicle


class FuelTransactionType(str, enum.Enum):
    FILL = "FILL"
    ADJUSTMENT = "ADJUSTMENT"


class FuelSource(str, enum.Enum):
    SENSOR = "SENSOR"
    ESTIMATED = "ESTIMATED"
    MANUAL = "MANUAL"


class FuelStateReliability(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class FuelState(Base):
    """
    Represents the latest known business state of a vehicle's fuel.
    """
    __tablename__ = "fuel_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), unique=True, nullable=False, index=True
    )
    current_level: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="Current known fuel level in liters"
    )
    
    # Traceability
    source: Mapped[FuelSource] = mapped_column(
        Enum(FuelSource, native_enum=False, length=50),
        nullable=False,
        default=FuelSource.ESTIMATED,
        comment="Origin of this state"
    )
    reliability: Mapped[FuelStateReliability] = mapped_column(
        Enum(FuelStateReliability, native_enum=False, length=50),
        nullable=False,
        default=FuelStateReliability.UNKNOWN,
        comment="Business-oriented reliability of the measurement"
    )
    last_operational_event_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Reference ID from the origin (e.g., OperationalEvent ID)"
    )

    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle")

    def __repr__(self) -> str:
        return f"<FuelState(vehicle={self.vehicle_id}, level={self.current_level}L, source={self.source.value}, reliability={self.reliability.value})>"


class FuelTransaction(Base):
    """
    Historical ledger of fuel changes (fills, adjustments).
    """
    __tablename__ = "fuel_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=False, index=True
    )
    transaction_type: Mapped[FuelTransactionType] = mapped_column(
        Enum(FuelTransactionType, native_enum=False, length=50),
        nullable=False, index=True
    )
    amount_liters: Mapped[float] = mapped_column(
        Float, nullable=False,
        comment="Amount of fuel changed in liters (can be positive or negative for adjustments)"
    )
    
    # Traceability
    origin_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    origin_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        comment="When the transaction occurred"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle")

    def __repr__(self) -> str:
        return f"<FuelTransaction(id={self.id}, vehicle={self.vehicle_id}, type={self.transaction_type.value}, amount={self.amount_liters}L)>"
