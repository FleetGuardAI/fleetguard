"""
FleetGuard — Expense Domain Schemas
Pydantic schemas for the Expense REST APIs.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from models.expense_domain import ExpenseCategory, ExpenseStatus


class ExpenseResponse(BaseModel):
    """
    Read-only representation of an Expense record.
    """
    id: int
    business_id: str
    
    category: ExpenseCategory
    amount: float
    currency: str
    status: ExpenseStatus
    
    expense_date: datetime
    description: Optional[str] = None
    receipt_reference: Optional[str] = None
    
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    trip_id: Optional[int] = None
    maintenance_id: Optional[int] = None
    
    origin_type: str
    origin_id: str
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
