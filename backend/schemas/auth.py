"""
FleetGuard — Authentication Pydantic Schemas

Defines request and response schemas for the authentication endpoints.
These schemas are shared between the API and front-end interface,
adhering strictly to Pydantic v2 patterns.
"""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from models.company import CompanyStatus
from models.user import UserRole


class CompanyRegistrationRequest(BaseModel):
    """Payload for public company registration."""

    company_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Legal or trading name of the company",
        examples=["FleetGuard Logistics Ltd"]
    )
    owner_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name of the company owner/primary admin",
        examples=["Rajesh Kumar"]
    )
    mobile_number: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Owner's mobile number; used for registration and primary admin login",
        examples=["+919876543210"]
    )
    email: Optional[str] = Field(
        None,
        description="Optional company contact email address",
        examples=["owner@fleetguard.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password for the primary admin user (minimum 8 characters)"
    )
    confirm_password: str = Field(
        ...,
        description="Must match password field exactly"
    )

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, v: str) -> str:
        # Validates E.164 phone number format or standard national digits
        pattern = r"^\+?[1-9]\d{9,14}$"
        if not re.match(pattern, v):
            raise ValueError(
                "Mobile number must be in a valid format (e.g., +919876543210 or 9876543210)"
            )
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email address format")
        return v

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "CompanyRegistrationRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    """Payload for login by email or mobile number."""

    email: Optional[str] = Field(None, description="User's registered email address")
    mobile_number: Optional[str] = Field(None, description="User's registered mobile number")
    password: str = Field(..., description="User's password")
    remember_me: bool = Field(False, description="Keep session active for longer duration")

    @model_validator(mode="after")
    def verify_identifier_supplied(self) -> "LoginRequest":
        if not self.email and not self.mobile_number:
            raise ValueError("Either email or mobile_number must be provided")
        return self


class TokenResponse(BaseModel):
    """JWT Access Token response payload."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token scheme (typically bearer)")


class ForgotPasswordRequest(BaseModel):
    """Start forgot-password flow using email or mobile identifier."""

    identifier: str = Field(..., min_length=3, max_length=255)


class ResetPasswordRequest(BaseModel):
    """Complete reset-password flow with one-time reset token."""

    reset_token: str = Field(..., min_length=16)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class ForgotPasswordResponse(BaseModel):
    """Response payload for forgot-password initiation."""

    message: str
    reset_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class GenericMessageResponse(BaseModel):
    """Simple response for mutation endpoints that only return status text."""

    message: str


class CompanyOut(BaseModel):
    """Safe public representation of a Company."""

    id: int
    company_name: str
    owner_name: str
    mobile_number: str
    email: Optional[str]
    status: CompanyStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    """Safe public representation of a User."""

    id: int
    company_id: int
    full_name: str
    mobile_number: str
    email: Optional[str]
    role: UserRole
    is_active: bool
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RegisterCompanyResponse(BaseModel):
    """Response payload returned after successful company registration."""

    company: CompanyOut
    user: UserOut
    token: TokenResponse

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    """Response payload for current authenticated user details."""

    user: UserOut
    company: CompanyOut
    role: UserRole

    model_config = {"from_attributes": True}
