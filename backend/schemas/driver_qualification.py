"""
FleetGuard — Driver Qualification Pydantic Schemas
Defines request and response schemas for structured driver qualifications,
driving license categories, validity tracking, and verification workflows.
"""

from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field

from models.driver_qualification import (
    QualificationType,
    LicenseClass,
    QualificationVerificationStatus,
)


class DriverQualificationBase(BaseModel):
    qualification_type: QualificationType = Field(
        default=QualificationType.DRIVING_LICENSE,
        description="Type of qualification / endorsement"
    )
    license_class: Optional[LicenseClass] = Field(
        default=None,
        description="License class if applicable (LMV, MGV, HGV, HMV, HAZMAT, TANKER)"
    )
    certificate_number: str = Field(
        ..., min_length=1, max_length=100,
        description="License / certificate identification number"
    )
    issuing_authority: Optional[str] = Field(
        default=None, max_length=150,
        description="Issuing authority or RTO"
    )
    issue_date: Optional[date] = Field(
        default=None,
        description="Date of issuance"
    )
    expiry_date: Optional[date] = Field(
        default=None,
        description="Date of expiration"
    )
    evidence_url: Optional[str] = Field(
        default=None, max_length=500,
        description="Document URL or photo proof"
    )


class DriverQualificationCreate(DriverQualificationBase):
    driver_id: Optional[int] = Field(
        default=None,
        description="ID of the driver if creating from company/admin endpoint"
    )


class DriverQualificationUpdate(BaseModel):
    qualification_type: Optional[QualificationType] = None
    license_class: Optional[LicenseClass] = None
    certificate_number: Optional[str] = Field(None, min_length=1, max_length=100)
    issuing_authority: Optional[str] = Field(None, max_length=150)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    evidence_url: Optional[str] = Field(None, max_length=500)


class DriverQualificationVerifyRequest(BaseModel):
    verification_status: QualificationVerificationStatus = Field(
        ...,
        description="Verification decision (VERIFIED or REJECTED)"
    )
    rejection_reason: Optional[str] = Field(
        default=None, max_length=500,
        description="Mandatory or recommended note when rejected"
    )


class DriverQualificationResponse(BaseModel):
    id: int
    driver_id: int
    company_id: int
    qualification_type: QualificationType
    license_class: Optional[LicenseClass] = None
    certificate_number: str
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    verification_status: QualificationVerificationStatus
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    evidence_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
