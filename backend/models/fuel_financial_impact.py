"""
FleetGuard — Fuel Financial Impact ORM Model
Stores the monetary interpretation of a verified fuel anomaly.
"""

from datetime import datetime
import enum
from sqlalchemy import Integer, String, Float, Enum, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional, Dict, Any

from database import Base
from models.derived_fuel_metrics import EntityTypeEnum, FuelMetricType

class FuelPriceSource(str, enum.Enum):
    ACTUAL_PURCHASE_PRICE = "ACTUAL_PURCHASE_PRICE"
    VOLUME_WEIGHTED_PURCHASE_PRICE = "VOLUME_WEIGHTED_PURCHASE_PRICE"
    VERIFIED_HISTORICAL_REFERENCE = "VERIFIED_HISTORICAL_REFERENCE"

# Use JSONB for Postgres, fallback to JSON for SQLite
JsonType = JSON().with_variant(JSONB, "postgresql")

class FinancialImpact(Base):
    __tablename__ = "fuel_financial_impacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[EntityTypeEnum] = mapped_column(Enum(EntityTypeEnum, name="impact_entity_type"), nullable=False, index=True)
    metric_type: Mapped[FuelMetricType] = mapped_column(Enum(FuelMetricType, name="impact_metric_type"), nullable=False, index=True)

    # --- Generic Fields ---
    baseline_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    observed_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    domain_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)

    # --- Legacy Fuel Fields (Retained for phased migration dual-write) ---
    baseline_efficiency: Mapped[float] = mapped_column(Float, nullable=False)
    observed_efficiency: Mapped[float] = mapped_column(Float, nullable=False)

    distance: Mapped[float] = mapped_column(Float, nullable=False)
    
    expected_fuel_liters: Mapped[float] = mapped_column(Float, nullable=False)
    implied_fuel_liters: Mapped[float] = mapped_column(Float, nullable=False)
    excess_fuel_liters: Mapped[float] = mapped_column(Float, nullable=False)

    fuel_price_per_liter: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_price_source: Mapped[FuelPriceSource] = mapped_column(Enum(FuelPriceSource, name="fuel_price_source"), nullable=False)
    
    # --- Universal Financial Fields ---
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    estimated_financial_exposure: Mapped[float] = mapped_column(Float, nullable=False)

    anomaly_reference: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    baseline_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    observation_reference: Mapped[str] = mapped_column(String(255), nullable=False)

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    calculation_method: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<FinancialImpact(anomaly={self.anomaly_reference}, exposure={self.estimated_financial_exposure})>"

# Backward compatibility alias
FuelFinancialImpact = FinancialImpact
