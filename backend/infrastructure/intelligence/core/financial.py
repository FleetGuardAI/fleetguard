import math
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from models.derived_fuel_metrics import EntityTypeEnum, FuelMetricType


class GenericFinancialImpactResult(BaseModel):
    """
    Domain-agnostic contract for the result of a financial impact calculation.
    """
    status: str = Field(..., description="SUCCESS or INSUFFICIENT_DATA")
    reason: Optional[str] = None
    
    entity_id: Optional[str] = None
    entity_type: Optional[EntityTypeEnum] = None
    metric_type: Optional[FuelMetricType] = None
    
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    
    estimated_financial_exposure: Optional[float] = None
    currency: str = "INR"
    
    domain_context: Optional[Dict[str, Any]] = None
    
    anomaly_reference: Optional[str] = None
    baseline_reference: Optional[str] = None
    observation_reference: Optional[str] = None
    
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    calculation_method: Optional[str] = None


class GenericFinancialImpactEngine:
    """
    Core validation for generic financial results.
    Does NOT compute domain-specific mathematics.
    """
    def validate_and_construct(self, payload: dict) -> GenericFinancialImpactResult:
        """
        Validates core mathematical soundness of exposure values and constructs the result.
        Ensures exposure is non-negative and finite.
        """
        status = payload.get("status")
        if status != "SUCCESS":
            return GenericFinancialImpactResult(**payload)
            
        exposure = payload.get("estimated_financial_exposure")
        
        # Ensure finite exposure
        if exposure is None or not math.isfinite(exposure):
            return GenericFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="NON_FINITE_FINANCIAL_EXPOSURE"
            )
            
        # Ensure non-negative exposure
        if exposure < 0:
            payload["estimated_financial_exposure"] = 0.0
            
        # Ensure finite baseline and observed values
        base_val = payload.get("baseline_value")
        obs_val = payload.get("observed_value")
        
        if base_val is not None and not math.isfinite(base_val):
             payload["baseline_value"] = None
        if obs_val is not None and not math.isfinite(obs_val):
             payload["observed_value"] = None
             
        # Initialize domain context if missing
        if "domain_context" not in payload or payload["domain_context"] is None:
            payload["domain_context"] = {}
            
        return GenericFinancialImpactResult(**payload)
