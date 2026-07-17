"""
FleetGuard — Driver Pydantic Schemas
Request/response models for the Drivers API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class DriverBase(BaseModel):
    """Shared driver fields."""
    name: str = Field(
        ..., min_length=1, max_length=150,
        examples=["Rajesh Kumar"],
        description="Full name of the driver"
    )
    phone_number: str = Field(
        ..., min_length=10, max_length=20,
        examples=["+919876543210"],
        description="WhatsApp phone number in E.164 format"
    )


class DriverCreate(DriverBase):
    """Schema for registering a new driver."""
    avatar_url: Optional[str] = None


class DriverUpdate(BaseModel):
    """Schema for updating driver info. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    rating: Optional[float] = Field(None, ge=0, le=5)
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None


class DriverResponse(DriverBase):
    """Schema for driver API responses."""
    id: int
    company_id: int
    risk_score: float = Field(description="Risk score 0-100")
    rating: float = Field(description="Performance rating 0-5")
    total_trips: int
    total_expenses: float = Field(description="Cumulative approved expenses in INR")
    avatar_url: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class DriverScoreResponse(BaseModel):
    """Response for the scoring engine recalculation."""
    driver_id: int
    old_score: float
    new_score: float
    factors: dict = Field(
        description="Breakdown of scoring factors",
        examples=[{
            "rejected_receipts": 3,
            "high_risk_submissions": 2,
            "theft_associations": 1,
            "weighted_score": 42.5,
        }]
    )
