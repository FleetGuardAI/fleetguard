from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from models.fuel_root_cause import RootCauseType, EvidenceStrength
from models.fuel_anomaly import AnomalyDirection, AnomalySeverity
from models.fuel_financial_impact import FuelPriceSource
from infrastructure.intelligence.fuel_domain.financial.summary_schemas import TruckFinancialIntelligence

class FuelAnomalyResponse(BaseModel):
    anomaly_reference: str
    observed_value: float
    baseline_value: float
    deviation_percent: float
    direction: AnomalyDirection
    severity: AnomalySeverity
    period_start: datetime
    period_end: datetime

class FuelFinancialImpactResponse(BaseModel):
    anomaly_reference: str
    estimated_financial_exposure: float
    excess_fuel_liters: float
    fuel_price_per_liter: float
    fuel_price_source: FuelPriceSource
    period_start: datetime
    period_end: datetime

class EvidenceItemResponse(BaseModel):
    cause_type: RootCauseType
    evidence_status: str
    evidence_strength: EvidenceStrength
    explanation: Optional[str]
    source_references: List[str]

class ContributingFactorDetail(BaseModel):
    anomaly_reference: str
    possible_contributing_factors: List[EvidenceItemResponse]

class TruckIntelligenceDetailResponse(BaseModel):
    summary: TruckFinancialIntelligence
    anomalies: List[FuelAnomalyResponse]
    financial_impacts: List[FuelFinancialImpactResponse]
    contributing_factors: List[ContributingFactorDetail]
