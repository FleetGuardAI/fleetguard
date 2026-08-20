"""
FleetGuard — Derived Fuel Metrics ORM Model
Explicitly marked as derived intelligence. Does not overwrite operational data.
"""

from sqlalchemy import Integer, String, Float, Enum, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import enum
from datetime import datetime, timezone

from database import Base

class DataQuality(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"

class MeasurementType(str, enum.Enum):
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    ESTIMATED = "ESTIMATED"

class FuelSource(str, enum.Enum):
    FUEL_SENSOR = "FUEL_SENSOR"
    FUEL_TRANSACTION = "FUEL_TRANSACTION"
    ODOMETER_FUEL = "ODOMETER_FUEL"
    MANUAL_ENTRY = "MANUAL_ENTRY"
    EXTERNAL_TELEMATICS = "EXTERNAL_TELEMATICS"
    ESTIMATED = "ESTIMATED"

class FuelMetricType(str, enum.Enum):
    FUEL_EFFICIENCY = "FUEL_EFFICIENCY"
    FUEL_CONSUMPTION = "FUEL_CONSUMPTION"

class EntityTypeEnum(str, enum.Enum):
    TRUCK = "TRUCK"
    TRIP = "TRIP"
    DRIVER = "DRIVER"
    FLEET = "FLEET"

class DerivedFuelMetric(Base):
    """
    Persisted derived fuel intelligence metrics.
    Only successful calculations are stored here.
    """
    __tablename__ = "derived_fuel_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[EntityTypeEnum] = mapped_column(Enum(EntityTypeEnum, name="metric_entity_type"), nullable=False, index=True)
    
    metric_type: Mapped[FuelMetricType] = mapped_column(Enum(FuelMetricType, name="fuel_metric_type"), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    
    source: Mapped[FuelSource] = mapped_column(Enum(FuelSource, name="fuel_source_type"), nullable=False)
    quality: Mapped[DataQuality] = mapped_column(Enum(DataQuality, name="fuel_data_quality"), nullable=False)
    measurement_type: Mapped[MeasurementType] = mapped_column(Enum(MeasurementType, name="fuel_measurement_type"), nullable=False)
    
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Traceability to operational data")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_derived_fuel_metrics_entity_period", "entity_type", "entity_id", "period_start", "period_end"),
    )
