from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from models.derived_fuel_metrics import EntityTypeEnum, FuelMetricType
from models.fuel_anomaly import AnomalyDirection, AnomalySeverity, AnomalyStatus

class FuelAnomalyResult(BaseModel):
    """
    Result of an anomaly calculation attempt.
    """
    status: AnomalyStatus = Field(..., description="ANOMALY, NORMAL, or INSUFFICIENT_DATA")
    reason: Optional[str] = None
    
    entity_id: Optional[str] = None
    entity_type: Optional[EntityTypeEnum] = None
    metric_type: Optional[FuelMetricType] = None
    
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    
    deviation_percent: Optional[float] = None
    
    direction: Optional[AnomalyDirection] = None
    severity: Optional[AnomalySeverity] = None
    
    baseline_reference: Optional[str] = None
    observation_reference: Optional[str] = None
    
    detected_at: Optional[datetime] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
