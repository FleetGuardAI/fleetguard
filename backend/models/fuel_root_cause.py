"""
FleetGuard — Fuel Root Cause Analysis Models
"""

from sqlalchemy import Integer, String, Float, Enum, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List
from datetime import datetime
import enum

from database import Base
from models.derived_fuel_metrics import EntityTypeEnum

class RootCauseType(str, enum.Enum):
    EXCESSIVE_IDLE = "EXCESSIVE_IDLE"
    HIGH_SPEED = "HIGH_SPEED"
    EXCESS_DISTANCE = "EXCESS_DISTANCE"
    FUEL_EVENT_ANOMALY = "FUEL_EVENT_ANOMALY"
    VEHICLE_MAINTENANCE = "VEHICLE_MAINTENANCE"
    DRIVER_BEHAVIOUR = "DRIVER_BEHAVIOUR"
    UNKNOWN = "UNKNOWN"

class EvidenceStatus(str, enum.Enum):
    SUPPORTING = "SUPPORTING"
    NEUTRAL = "NEUTRAL"
    CONTRADICTING = "CONTRADICTING"
    UNAVAILABLE = "UNAVAILABLE"

class EvidenceStrength(str, enum.Enum):
    NO_EVIDENCE = "NO_EVIDENCE"
    WEAK_SUPPORT = "WEAK_SUPPORT"
    MODERATE_SUPPORT = "MODERATE_SUPPORT"
    STRONG_SUPPORT = "STRONG_SUPPORT"

class ContributingFactorAnalysis(Base):
    __tablename__ = "fuel_root_cause_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    anomaly_reference: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    financial_impact_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[EntityTypeEnum] = mapped_column(Enum(EntityTypeEnum, native_enum=False, length=50), nullable=False)

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPLETED")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    evidence_items: Mapped[List["ContributingFactorEvidence"]] = relationship("ContributingFactorEvidence", back_populates="analysis", cascade="all, delete-orphan")

# Compatibility Alias
FuelRootCauseAnalysis = ContributingFactorAnalysis

class ContributingFactorEvidence(Base):
    __tablename__ = "fuel_root_cause_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    analysis_id: Mapped[int] = mapped_column(ForeignKey("fuel_root_cause_analyses.id"), nullable=False, index=True)
    analysis: Mapped["ContributingFactorAnalysis"] = relationship("ContributingFactorAnalysis", back_populates="evidence_items")
    
    cause_type: Mapped[RootCauseType] = mapped_column(Enum(RootCauseType, native_enum=False, length=50), nullable=False)
    evidence_status: Mapped[EvidenceStatus] = mapped_column(Enum(EvidenceStatus, native_enum=False, length=50), nullable=False)
    evidence_strength: Mapped[EvidenceStrength] = mapped_column(Enum(EvidenceStrength, native_enum=False, length=50), nullable=False)
    
    evidence_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    baseline_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deviation_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source_references: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Comma-separated IDs")
    
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

# Compatibility Alias
FuelRootCauseEvidence = ContributingFactorEvidence
