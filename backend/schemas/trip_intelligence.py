"""
FleetGuard — Trip Intelligence Schemas
Pydantic response models for the Trip Intelligence API.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


# ===========================================================================
# Enumerations
# ===========================================================================

class InsightSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class InsightType(str, Enum):
    FUEL_ANOMALY = "FUEL_ANOMALY"
    EXPENSE_ANOMALY = "EXPENSE_ANOMALY"
    DURATION_ANOMALY = "DURATION_ANOMALY"
    DISTANCE_ANOMALY = "DISTANCE_ANOMALY"
    DETENTION = "DETENTION"
    EMPTY_RETURN = "EMPTY_RETURN"
    COST_OVERRUN = "COST_OVERRUN"
    REVENUE_SHORTFALL = "REVENUE_SHORTFALL"


class DataQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


# ===========================================================================
# Sub-Models
# ===========================================================================

class FinancialSummary(BaseModel):
    """Top-level financial KPIs for the trip."""
    revenue: Optional[float] = None
    total_cost: Optional[float] = None
    net_profit: Optional[float] = None
    profit_margin_pct: Optional[float] = None
    cost_per_km: Optional[float] = None
    revenue_per_km: Optional[float] = None
    currency: str = "INR"
    has_sufficient_data: bool = False


class CostBreakdownItem(BaseModel):
    """Single category in the cost breakdown."""
    category: str
    category_label: str
    amount: float
    percentage: float
    currency: str = "INR"


class PlannedVsActualItem(BaseModel):
    """Single metric comparing planned vs actual."""
    metric: str
    metric_label: str
    planned: Optional[float] = None
    actual: Optional[float] = None
    variance: Optional[float] = None
    variance_pct: Optional[float] = None
    unit: str = ""
    severity: InsightSeverity = InsightSeverity.INFO
    has_data: bool = False


class ProfitLossContributor(BaseModel):
    """Single contributor to profit loss or gain."""
    rank: int
    title: str
    description: str
    impact_amount: Optional[float] = None
    is_estimate: bool = False
    currency: str = "INR"
    severity: InsightSeverity = InsightSeverity.WARNING
    evidence_refs: List[str] = Field(default_factory=list)


class EfficiencySubScore(BaseModel):
    """Sub-component of the overall efficiency score."""
    name: str
    label: str
    score: Optional[float] = None
    max_score: float = 100.0
    has_data: bool = False


class TripEfficiencyScore(BaseModel):
    """Overall trip efficiency score with breakdown."""
    overall_score: Optional[float] = None
    max_score: float = 100.0
    grade: Optional[str] = None
    explanation: Optional[str] = None
    sub_scores: List[EfficiencySubScore] = Field(default_factory=list)
    data_quality: DataQuality = DataQuality.INSUFFICIENT
    has_sufficient_data: bool = False


class HistoricalComparison(BaseModel):
    """Single historical comparison metric."""
    metric: str
    metric_label: str
    current_value: Optional[float] = None
    comparison_value: Optional[float] = None
    comparison_label: str = ""
    variance_pct: Optional[float] = None
    unit: str = ""
    is_favorable: Optional[bool] = None
    sample_size: int = 0


class EvidenceRef(BaseModel):
    """Reference to a piece of supporting evidence."""
    evidence_type: str
    label: str
    detail: Optional[str] = None


class Insight(BaseModel):
    """A single intelligence insight detected from trip data."""
    insight_type: InsightType
    severity: InsightSeverity
    title: str
    description: str
    impact_amount: Optional[float] = None
    is_estimate: bool = False
    currency: str = "INR"
    evidence: List[EvidenceRef] = Field(default_factory=list)


class Recommendation(BaseModel):
    """An actionable recommendation based on detected anomalies."""
    priority: int
    title: str
    description: str
    related_insight_type: Optional[InsightType] = None


# ===========================================================================
# Top-Level Response
# ===========================================================================

class TripIntelligenceResponse(BaseModel):
    """Complete Trip Intelligence response for a single trip."""
    trip_id: int
    trip_business_id: str
    trip_status: str

    # Section 1: Financial Summary
    financial_summary: FinancialSummary

    # Section 2: Cost Breakdown
    cost_breakdown: List[CostBreakdownItem] = Field(default_factory=list)

    # Section 3: Planned vs Actual
    planned_vs_actual: List[PlannedVsActualItem] = Field(default_factory=list)

    # Section 4: Profit Loss Contributors ("Why did we lose money?")
    profit_loss_contributors: List[ProfitLossContributor] = Field(default_factory=list)

    # Section 5: Trip Efficiency Score
    efficiency_score: TripEfficiencyScore

    # Section 6: Intelligence Insights
    insights: List[Insight] = Field(default_factory=list)

    # Section 7: Historical Comparisons
    historical_comparisons: List[HistoricalComparison] = Field(default_factory=list)

    # Section 8: Recommendations
    recommendations: List[Recommendation] = Field(default_factory=list)

    # Metadata
    data_quality: DataQuality = DataQuality.INSUFFICIENT
    data_sources_used: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
