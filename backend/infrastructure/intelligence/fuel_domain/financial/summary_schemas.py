from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

from models.fuel_root_cause import RootCauseType, EvidenceStrength
from models.fuel_anomaly import AnomalySeverity

class ContributingFactorSummary(BaseModel):
    cause_type: RootCauseType
    affected_truck_count: int
    total_estimated_exposure: float
    highest_observed_strength: EvidenceStrength
    strength_counts: Dict[EvidenceStrength, int]

class TruckFinancialIntelligence(BaseModel):
    truck_id: str
    estimated_exposure: float
    excess_fuel_liters: float
    anomaly_count: int
    worst_deviation_percent: float
    severity: AnomalySeverity
    top_contributing_factor: RootCauseType
    top_contributing_strength: EvidenceStrength
    period_start: datetime
    period_end: datetime
    data_conflict: bool = False

class FleetFinancialIntelligenceSummary(BaseModel):
    period_start: datetime
    period_end: datetime
    fleet_id: str
    
    total_trucks: int
    trucks_with_sufficient_intelligence: int
    trucks_with_insufficient_data: int
    affected_trucks: int
    trucks_without_anomaly: int
    
    total_estimated_exposure: float
    total_excess_fuel_liters: float
    average_exposure_per_affected_truck: float
    
    top_exposures: List[TruckFinancialIntelligence]
    contributing_factor_summary: List[ContributingFactorSummary]
