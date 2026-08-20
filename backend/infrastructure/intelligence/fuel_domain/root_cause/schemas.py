from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from models.derived_fuel_metrics import EntityTypeEnum
from models.fuel_root_cause import RootCauseType, EvidenceStatus, EvidenceStrength

class RootCauseEvidenceResult(BaseModel):
    cause_type: RootCauseType
    evidence_status: EvidenceStatus
    evidence_strength: EvidenceStrength
    evidence_value: Optional[float] = None
    baseline_value: Optional[float] = None
    deviation_percent: Optional[float] = None
    unit: Optional[str] = None
    explanation: str
    source_references: Optional[str] = None

class RootCauseAnalysisResult(BaseModel):
    status: str
    entity_id: str
    entity_type: EntityTypeEnum
    anomaly_reference: str
    financial_impact_reference: Optional[str] = None
    period_start: datetime
    period_end: datetime
    candidate_causes: List[RootCauseEvidenceResult]
