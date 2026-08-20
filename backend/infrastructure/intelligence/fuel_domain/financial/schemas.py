from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from models.derived_fuel_metrics import EntityTypeEnum, FuelMetricType
from models.fuel_financial_impact import FuelPriceSource

class FuelFinancialImpactResult(BaseModel):
    status: str = Field(..., description="SUCCESS or INSUFFICIENT_DATA")
    reason: Optional[str] = None
    
    entity_id: Optional[str] = None
    entity_type: Optional[EntityTypeEnum] = None
    metric_type: Optional[FuelMetricType] = None
    
    baseline_efficiency: Optional[float] = None
    observed_efficiency: Optional[float] = None
    
    distance: Optional[float] = None
    distance_unit: str = "KM"
    
    expected_fuel_liters: Optional[float] = None
    implied_fuel_liters: Optional[float] = None
    excess_fuel_liters: Optional[float] = None
    
    fuel_price_per_liter: Optional[float] = None
    fuel_price_source: Optional[FuelPriceSource] = None
    currency: str = "INR"
    
    estimated_financial_exposure: Optional[float] = None
    
    anomaly_reference: Optional[str] = None
    baseline_reference: Optional[str] = None
    observation_reference: Optional[str] = None
    
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    calculation_method: Optional[str] = None
