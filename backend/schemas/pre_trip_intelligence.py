"""
FleetGuard — Pre-Trip Intelligence Schemas

Pydantic models for the Pre-Trip intelligence evaluation API.
These are consumed identically by Owner Website and Owner App.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from enum import Enum


# ===========================================================================
# Enumerations
# ===========================================================================

class RecommendationDecision(str, Enum):
    TAKE = "TAKE"
    REVIEW = "REVIEW"
    AVOID = "AVOID"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class SuitabilityStatus(str, Enum):
    SUITABLE = "SUITABLE"
    MARGINAL = "MARGINAL"
    UNSUITABLE = "UNSUITABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class RecommendationOutcomeType(str, Enum):
    OUTPERFORMED = "OUTPERFORMED"
    MET_EXPECTATION = "MET_EXPECTATION"
    UNDERPERFORMED = "UNDERPERFORMED"
    LOSS = "LOSS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


# ===========================================================================
# Sub-Models
# ===========================================================================

class Assumption(BaseModel):
    """A single assumption used in the intelligence calculation."""
    metric: str
    value: float
    unit: str
    source: str           # "vehicle_historical", "fleet_average", "system_default", "user_input"
    confidence: str       # HIGH / MEDIUM / LOW
    sample_size: Optional[int] = None


class RiskFactor(BaseModel):
    """A single factor contributing to trip risk."""
    factor: str
    severity: str         # LOW / MEDIUM / HIGH
    description: str


class RecommendationReason(BaseModel):
    """A single reason supporting or against the recommendation."""
    factor_type: str      # "positive" or "negative"
    description: str


class SuitabilityAssessment(BaseModel):
    """Vehicle or driver suitability evaluation."""
    status: SuitabilityStatus
    reasons: List[str] = Field(default_factory=list)


class CostComponent(BaseModel):
    """A single component of the expected cost breakdown."""
    category: str
    label: str
    amount: float
    source: str           # "calculated", "estimated", "default"
    currency: str = "INR"


# ===========================================================================
# Request
# ===========================================================================

class PreTripEvaluateRequest(BaseModel):
    """Request body for progressive pre-trip intelligence evaluation."""
    # Step 1: Locations (required to start routing)
    origin_location: Optional[str] = None
    destination_location: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    
    # Pre-calculated route info (if frontend already called /routes/calculate)
    route_distance_km: Optional[float] = None
    route_duration_hours: Optional[float] = None
    
    # Step 2: Assignments (optional for initial evaluation)
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    
    # Step 3: Timings & Financials
    planned_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    revenue: Optional[float] = None
    cargo_weight: Optional[float] = None
    
    # Legacy fields (optional now, mostly auto-derived)
    planned_distance: Optional[float] = None
    planned_cost: Optional[float] = None
    planned_fuel_liters: Optional[float] = None

# ===========================================================================
# Response
# ===========================================================================

class PreTripIntelligenceResponse(BaseModel):
    """
    Complete pre-trip intelligence evaluation.
    Consumed by both Owner Website and Owner App.
    """

    # --- Decision ---
    recommendation: RecommendationDecision
    recommendation_reasons: List[RecommendationReason] = Field(default_factory=list)

    # --- Route & Economics ---
    expected_distance: Optional[float] = None
    expected_duration_hours: Optional[float] = None
    route_polyline: Optional[str] = None
    
    expected_fuel_liters: Optional[float] = None
    expected_fuel_cost: Optional[float] = None
    expected_toll: Optional[float] = None
    expected_driver_cost: Optional[float] = None
    expected_other_cost: Optional[float] = None
    expected_total_cost: Optional[float] = None
    expected_revenue: Optional[float] = None
    expected_profit: Optional[float] = None
    expected_margin_pct: Optional[float] = None
    minimum_recommended_freight: Optional[float] = None

    # --- Cost Breakdown ---
    cost_breakdown: List[CostComponent] = Field(default_factory=list)

    # --- Risk & Confidence ---
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    confidence_level: ConfidenceLevel = ConfidenceLevel.INSUFFICIENT
    confidence_reasons: List[str] = Field(default_factory=list)

    # --- Suitability ---
    vehicle_suitability: Optional[SuitabilityAssessment] = None
    driver_suitability: Optional[SuitabilityAssessment] = None

    # --- Transparency ---
    assumptions: List[Assumption] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # --- Versioning ---
    intelligence_version: str = "trip-intelligence-v1"
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)
