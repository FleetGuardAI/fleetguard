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
    
    # Approval/Rejection tracking
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpenseApproveRequest(BaseModel):
    """Request body for approving an expense."""
    pass


class ExpenseRejectRequest(BaseModel):
    """Request body for rejecting an expense. Rejection reason is mandatory."""
    rejection_reason: str = Field(..., min_length=1, max_length=1000, description="Reason for rejecting this expense claim")
