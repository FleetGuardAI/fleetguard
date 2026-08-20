from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from models.derived_fuel_metrics import EntityTypeEnum, FuelMetricType, DataQuality
from models.entity_baseline import BaselineStatus

class BaselineResult(BaseModel):
    """
    Result of a baseline calculation attempt.
    """
    status: BaselineStatus = Field(..., description="VALID or INSUFFICIENT_DATA")
    reason: Optional[str] = None
    
    entity_id: str
    entity_type: EntityTypeEnum
    metric_type: FuelMetricType
    
    baseline_value: Optional[float] = None
    unit: Optional[str] = None
    sample_size: int
    calculation_method: Optional[str] = None
    data_quality: Optional[DataQuality] = None
    
    period_start: datetime
    period_end: datetime
