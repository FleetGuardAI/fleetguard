"""
FleetGuard — Live Trip Intelligence Schemas

Pydantic models for the Live Trip Intelligence API.
These are consumed identically by Owner Website and Owner App.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from enum import Enum


class TripHealthStatus(str, Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"


class DeviationSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Deviation(BaseModel):
    """A single metric deviation from expectations."""
    metric: str
    severity: DeviationSeverity
    expected: Optional[float]
    actual: Optional[float]
    variance_pct: Optional[float]
    description: str


class LiveTripIntelligenceResponse(BaseModel):
    """
    Live health and projected profitability for an IN_PROGRESS trip.
    """
    trip_id: int
    trip_business_id: str
    health_status: TripHealthStatus
    
    # --- Time & Distance ---
    expected_duration_hours: Optional[float] = None
    elapsed_hours: Optional[float] = None
    estimated_remaining_hours: Optional[float] = None
    expected_distance: Optional[float] = None
    actual_distance: Optional[float] = None
    
    # --- Economics ---
    expected_revenue: Optional[float] = None
    expected_total_cost: Optional[float] = None
    actual_cost_so_far: Optional[float] = None
    estimated_remaining_cost: Optional[float] = None
    projected_total_cost: Optional[float] = None
    
    expected_profit: Optional[float] = None
    projected_profit: Optional[float] = None
    profit_erosion: Optional[float] = None
    profit_erosion_pct: Optional[float] = None
    
    # --- Deviations & Context ---
    deviations: List[Deviation] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # --- Versioning ---
    intelligence_version: str
    snapshot_available: bool
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)
