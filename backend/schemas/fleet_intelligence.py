"""
FleetGuard — Fleet Intelligence Schemas
Defines the Pydantic models for the Fleet Intelligence API, ensuring that internal 
infrastructure representations do not leak to the frontend.
"""

from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DomainRiskCountsSchema(BaseModel):
    low_count: int
    medium_count: int
    high_count: int
    critical_count: int


class FleetDomainStatisticsSchema(BaseModel):
    fuel: DomainRiskCountsSchema
    driver: DomainRiskCountsSchema
    maintenance: DomainRiskCountsSchema
    tyre: DomainRiskCountsSchema
    route: DomainRiskCountsSchema
    compliance: DomainRiskCountsSchema


class FleetFindingSchema(BaseModel):
    finding_key: str
    severity: str
    summary: str
    metadata: Dict[str, Any]


class FleetInsightSchema(BaseModel):
    insight_key: str
    insight_type: str
    insight_strength: str
    summary: str


class FleetHealthResponse(BaseModel):
    fleet_id: str
    generated_at: datetime
    fleet_health_status: str
    vehicle_count: int
    operational_vehicle_count: int
    critical_vehicle_count: int
    fleet_summary: str
    fleet_findings: List[FleetFindingSchema]
    domain_statistics: FleetDomainStatisticsSchema
    fleet_insights: List[FleetInsightSchema]


# ==============================================================================
# EVIDENCE-GROUNDED FLEET INTELLIGENCE MODELS (P3)
# ==============================================================================

class FindingCategory(str, Enum):
    FLEET_HEALTH = "FLEET_HEALTH"
    FUEL_EFFICIENCY = "FUEL_EFFICIENCY"
    MAINTENANCE = "MAINTENANCE"
    TRIP_OPERATIONS = "TRIP_OPERATIONS"
    DATA_QUALITY = "DATA_QUALITY"


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class DataQualityStatus(str, Enum):
    RELIABLE = "RELIABLE"
    STALE_TELEMETRY = "STALE_TELEMETRY"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    INCOMPLETE_RECORDS = "INCOMPLETE_RECORDS"


class ActionHandoff(BaseModel):
    screen: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    route: str
    action_label: str


class EvidenceGroundedFinding(BaseModel):
    finding_id: str
    category: FindingCategory
    severity: FindingSeverity
    title: str
    summary: str
    entity_type: Optional[str] = None  # VEHICLE, TRIP, DRIVER, FLEET
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    observation_period: str
    measured_value: Optional[str] = None
    baseline_value: Optional[str] = None
    deviation_percent: Optional[float] = None
    evidence_records: List[str] = Field(default_factory=list)
    supporting_timestamps: List[str] = Field(default_factory=list)
    data_quality_status: DataQualityStatus = DataQualityStatus.RELIABLE
    confidence: str = "HIGH"  # HIGH, MEDIUM, LOW
    recommended_action: str
    limitations: Optional[str] = None
    action_handoff: Optional[ActionHandoff] = None


class TelemetryHealthSummary(BaseModel):
    fresh_count: int
    stale_count: int
    unavailable_count: int
    fresh_percentage: float


class MaintenanceHealthSummary(BaseModel):
    overdue_count: int
    due_soon_count: int
    up_to_date_count: int


class TripHealthSummary(BaseModel):
    in_progress_count: int
    delayed_count: int
    completed_last_30d: int


class FleetHealthOverview(BaseModel):
    company_id: int
    generated_at: datetime
    overall_health_status: str  # HEALTHY, ATTENTION_REQUIRED, CRITICAL
    total_vehicles: int
    active_vehicles: int
    maintenance_vehicles: int
    telemetry: TelemetryHealthSummary
    maintenance: MaintenanceHealthSummary
    trips: TripHealthSummary
    fuel_anomalies_count: int
    data_quality_flags_count: int
    key_findings: List[EvidenceGroundedFinding]


class FuelVehicleMetric(BaseModel):
    vehicle_id: int
    registration_number: str
    make_model: str
    distance_km: float
    fuel_liters: float
    km_per_liter: Optional[float] = None
    liters_per_100km: Optional[float] = None
    expense_amount: float
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None


class FuelEfficiencyAnalysis(BaseModel):
    company_id: int
    observation_period: str
    current_period_spend: float
    previous_period_spend: Optional[float] = None
    spend_change_pct: Optional[float] = None
    total_distance_km: float
    total_fuel_liters: float
    fleet_avg_km_per_liter: Optional[float] = None
    fleet_avg_liters_per_100km: Optional[float] = None
    data_quality_status: DataQualityStatus
    findings: List[EvidenceGroundedFinding]
    vehicle_metrics: List[FuelVehicleMetric]
    limitations: str


class MaintenancePrioritiesResponse(BaseModel):
    company_id: int
    total_overdue: int
    total_due_soon: int
    total_repeat_issues: int
    findings: List[EvidenceGroundedFinding]
    limitations: str


class TripPerformanceAnalysis(BaseModel):
    company_id: int
    observation_period: str
    total_trips_analyzed: int
    delayed_trips_count: int
    distance_anomalies_count: int
    unclosed_trips_count: int
    findings: List[EvidenceGroundedFinding]
    limitations: str


class DataQualityResponse(BaseModel):
    company_id: int
    total_vehicles_audited: int
    vehicles_with_fresh_gps: int
    vehicles_with_stale_gps: int
    vehicles_with_no_gps: int
    vehicles_with_missing_odometer: int
    trips_with_distance_gaps: int
    findings: List[EvidenceGroundedFinding]
    data_completeness_score: float  # 0 to 100%


class FleetAnomaliesResponse(BaseModel):
    company_id: int
    total_anomalies: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    anomalies: List[EvidenceGroundedFinding]
