"""
FleetGuard — Entity Baseline ORM Model
Stores successful baseline calculations to be used by the Anomaly Engine.
"""

from sqlalchemy import Integer, String, Float, Enum, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
import enum
from datetime import datetime, timezone

from database import Base
from models.derived_fuel_metrics import EntityTypeEnum, FuelMetricType, DataQuality

class BaselineStatus(str, enum.Enum):
    VALID = "VALID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class EntityBaseline(Base):
    """
    Persisted entity baseline metrics.
    Only successful/valid baselines are stored here.
    """
    __tablename__ = "entity_baselines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[EntityTypeEnum] = mapped_column(Enum(EntityTypeEnum, native_enum=False, length=50), nullable=False, index=True)
    metric_type: Mapped[FuelMetricType] = mapped_column(Enum(FuelMetricType, native_enum=False, length=50), nullable=False, index=True)
    
    baseline_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(50), nullable=False)
    data_quality: Mapped[DataQuality] = mapped_column(Enum(DataQuality, native_enum=False, length=50), nullable=False)
    
    status: Mapped[BaselineStatus] = mapped_column(Enum(BaselineStatus, native_enum=False, length=50), nullable=False, default=BaselineStatus.VALID)
    
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("entity_id", "entity_type", "metric_type", "period_start", "period_end"),
        Index("ix_entity_baselines_lookup", "entity_id", "entity_type", "metric_type"),
    )
