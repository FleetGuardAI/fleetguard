from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from models.derived_fuel_metrics import (
    DataQuality,
    MeasurementType,
    FuelSource,
    FuelMetricType,
    EntityTypeEnum,
)

class NormalizedFuelMetric(BaseModel):
    """
    Normalized representation of a calculated fuel metric.
    Must only be instantiated if the calculation was successful.
    """
    entity_id: str
    entity_type: EntityTypeEnum
    metric_type: FuelMetricType
    value: float
    unit: str
    source: FuelSource
    quality: DataQuality
    measurement_type: MeasurementType
    period_start: datetime
    period_end: datetime
    sample_size: int = 1
    source_reference: Optional[str] = None

class MetricCalculationResult(BaseModel):
    """
    Result of a metric calculation attempt by a provider.
    Distinguishes between successful calculation and failure states.
    """
    status: str = Field(..., description="SUCCESS, INSUFFICIENT_DATA, or UNSUPPORTED")
    reason: Optional[str] = None
    metric: Optional[NormalizedFuelMetric] = None
