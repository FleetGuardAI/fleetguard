"""
FleetGuard — Ticket (Expense) Pydantic Schemas
Request/response models for the Tickets/Expenses API.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class TicketCreate(BaseModel):
    """Schema for creating a ticket (typically from WhatsApp bot)."""
    truck_id: int
    driver_id: int
    issue_type: str = Field(
        ..., min_length=1, max_length=100,
        examples=["Tire Puncture"],
        description="Expense category"
    )
    vendor_name: Optional[str] = Field(None, max_length=200)
    amount: float = Field(
        ..., gt=0,
        examples=[500.0],
        description="Claimed amount in INR"
    )
    description: Optional[str] = None
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    location_name: Optional[str] = None
    receipt_url: Optional[str] = None
    expense_date: Optional[datetime] = None


class TicketUpdate(BaseModel):
    """Schema for updating a ticket."""
    issue_type: Optional[str] = Field(None, max_length=100)
    vendor_name: Optional[str] = Field(None, max_length=200)
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    status: Optional[str] = Field(
        None,
        pattern="^(pending|approved|rejected)$",
        description="Must be: pending, approved, or rejected"
    )
    risk_level: Optional[str] = Field(
        None,
        pattern="^(Low|Medium|High|Critical)$",
    )


class TicketApproval(BaseModel):
    """Schema for approving or rejecting a ticket."""
    action: str = Field(
        ...,
        pattern="^(approve|reject)$",
        examples=["approve"],
        description="Must be 'approve' or 'reject'"
    )
    rejection_reason: Optional[str] = Field(
        None, max_length=500,
        description="Required when rejecting"
    )


class TicketResponse(BaseModel):
    """Full ticket response for API and dashboard."""
    id: int
    truck_id: int
    driver_id: int
    issue_type: str
    vendor_name: Optional[str] = None
    amount: float
    fair_price: Optional[float] = None
    description: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_name: Optional[str] = None
    receipt_url: Optional[str] = None
    status: str
    risk_level: str
    risk_reasons: Optional[str] = None
    is_duplicate: bool
    expense_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    payout_reference: Optional[str] = None

    # Joined fields for dashboard display
    driver_name: Optional[str] = None
    truck_plate: Optional[str] = None

    model_config = {"from_attributes": True}


class DashboardKPIs(BaseModel):
    """Top-level KPI card data for the owner dashboard."""
    active_trucks: int = Field(description="Number of currently active trucks")
    pending_approvals: int = Field(description="Tickets awaiting owner decision")
    theft_alerts: int = Field(description="Unresolved fuel theft alerts")
    flagged_drivers: int = Field(description="Drivers with risk_score > 50")
    total_expenses_today: float = Field(description="Total approved expenses today in INR")
    total_expenses_month: float = Field(description="Total approved expenses this month")
