"""
Fuel Operations Domain - Projections
"""

import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class FuelBalanceSummary(BaseModel):
    vehicle_id: str
    current_balance_liters: float
    max_capacity_liters: Optional[float] = None

class FuelHistoryProjection(BaseModel):
    transaction_id: uuid.UUID
    vehicle_id: str
    transaction_type: str
    volume_liters: float
    timestamp: datetime
    driver_assignment_id: Optional[uuid.UUID] = None
    trip_id: Optional[uuid.UUID] = None
