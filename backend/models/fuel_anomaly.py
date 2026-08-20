"""
FleetGuard — Fuel Anomaly ORM Model
Stores strictly anomalous or observed intelligence against historical baselines.
"""

from sqlalchemy import Integer, String, Float, Enum, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
import enum
from datetime import datetime, timezone

from database import Base
from models.derived_fuel_metrics import EntityTypeEnum, FuelMetricType

class AnomalyDirection(str, enum.Enum):
    DEGRADATION = "DEGRADATION"
    IMPROVEMENT = "IMPROVEMENT"
    NORMAL = "NORMAL"

class AnomalySeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    NORMAL = "NORMAL"

class AnomalyStatus(str, enum.Enum):
    ANOMALY = "ANOMALY"
    NORMAL = "NORMAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class FuelAnomaly(Base):
    """
    Persisted fuel anomaly signal.
    """
    __tablename__ = "fuel_anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[EntityTypeEnum] = mapped_column(Enum(EntityTypeEnum, name="anomaly_entity_type"), nullable=False, index=True)
    metric_type: Mapped[FuelMetricType] = mapped_column(Enum(FuelMetricType, name="anomaly_fuel_metric_type"), nullable=False, index=True)
    
    baseline_value: Mapped[float] = mapped_column(Float, nullable=False)
    observed_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    deviation_percent: Mapped[float] = mapped_column(Float, nullable=False, doc="Actual percentage e.g. -12.42 for 12.42% degradation")
    
    direction: Mapped[AnomalyDirection] = mapped_column(Enum(AnomalyDirection, name="anomaly_direction"), nullable=False)
    severity: Mapped[AnomalySeverity] = mapped_column(Enum(AnomalySeverity, name="anomaly_severity"), nullable=False)
    status: Mapped[AnomalyStatus] = mapped_column(Enum(AnomalyStatus, name="anomaly_status"), nullable=False)
    
    baseline_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    observation_reference: Mapped[str] = mapped_column(String(255), nullable=False, index=True, doc="Unique reference to the observed metric event")
    
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("observation_reference", name="uix_fuel_anomaly_observation"),
        Index("ix_fuel_anomalies_lookup", "entity_id", "entity_type", "metric_type"),
    )
