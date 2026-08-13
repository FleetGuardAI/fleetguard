"""
FleetGuard — Fleet Intelligence Schemas
Defines the Pydantic models for the Fleet Intelligence API, ensuring that internal 
infrastructure representations do not leak to the frontend.
"""

from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel


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
