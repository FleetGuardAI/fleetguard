"""
Fuel Operations Domain - API Schemas
"""

from pydantic import BaseModel
from typing import List, Optional

class FuelBalanceResponse(BaseModel):
    vehicle_id: str
    current_balance_liters: float
    max_capacity_liters: Optional[float] = None

class FuelHistoryResponse(BaseModel):
    data: List[dict] # Would be a strongly typed List[FuelHistoryProjection] in a real app
    meta: dict
