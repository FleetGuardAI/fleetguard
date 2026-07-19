"""
Fleet Intelligence Engine - Fleet Health Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile, RiskLevel
from infrastructure.intelligence.cross_domain.models import FleetInsight


class FleetHealthStatus(str, Enum):
    """
    Categorical status representing the overall health and readiness of the fleet.
    """
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    CRITICAL = "CRITICAL"


class FleetFindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class FleetFinding(BaseModel):
    """
    Structured fleet-level finding derived from aggregating individual vehicle intelligence.
    Can be used deterministically for downstream presentation or rules engines.
    """
    finding_key: str
    severity: FleetFindingSeverity
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class DomainRiskCounts(BaseModel):
    """
    Risk distribution for a single domain across the fleet.
    """
    low_count: int = 0
    medium_count: int = 0
    high_count: int = 0
    critical_count: int = 0
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class FleetDomainStatistics(BaseModel):
    """
    Aggregated domain statistics for the entire fleet.
    """
    fuel: DomainRiskCounts = Field(default_factory=DomainRiskCounts)
    driver: DomainRiskCounts = Field(default_factory=DomainRiskCounts)
    maintenance: DomainRiskCounts = Field(default_factory=DomainRiskCounts)
    tyre: DomainRiskCounts = Field(default_factory=DomainRiskCounts)
    route: DomainRiskCounts = Field(default_factory=DomainRiskCounts)
    compliance: DomainRiskCounts = Field(default_factory=DomainRiskCounts)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class VehicleIntelligenceContext(BaseModel):
    """
    Dedicated context object providing a deterministic identifier (vehicle_id)
    alongside the intelligence profiles for that vehicle.
    """
    vehicle_id: str
    profiles: List[DomainRiskProfile] = Field(default_factory=list)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class FleetHealthReport(BaseModel):
    """
    Immutable report representing the aggregated operational health of the fleet.
    """
    report_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    fleet_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    fleet_health_status: FleetHealthStatus
    
    vehicle_count: int = 0
    operational_vehicle_count: int = 0
    critical_vehicle_count: int = 0
    
    fleet_summary: str
    fleet_findings: List[FleetFinding] = Field(default_factory=list)
    
    domain_statistics: FleetDomainStatistics
    fleet_insights: List[FleetInsight] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
