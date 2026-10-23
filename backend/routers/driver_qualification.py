"""
FleetGuard — Driver Qualification Router
API endpoints for driver qualifications, license classes, endorsements,
and authorized verification/rejection workflows.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.driver_domain import Driver
from models.driver_qualification import (
    DriverQualification,
    QualificationVerificationStatus,
    QualificationType,
    LicenseClass,
)
from models.user import User, UserRole
from schemas.driver_qualification import (
    DriverQualificationBase,
    DriverQualificationCreate,
    DriverQualificationUpdate,
    DriverQualificationVerifyRequest,
    DriverQualificationResponse,
)
from services.auth_service import get_current_user

logger = logging.getLogger("fleetguard.driver_qualification")

router = APIRouter(prefix="/v1", tags=["Driver Qualifications"])

VERIFICATION_PERMITTED_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.COMPANY_ADMIN,
    UserRole.FLEET_MANAGER,
    UserRole.ADMIN,
}


@router.post("/drivers/{driver_id}/qualifications", response_model=DriverQualificationResponse, status_code=status.HTTP_201_CREATED)
async def create_driver_qualification(
    driver_id: int,
    payload: DriverQualificationBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverQualificationResponse:
    """
    Create a qualification/endorsement for a driver.
    Ensures company tenant isolation.
    """
    driver = await db.get(Driver, driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Driver not found")

    qual = DriverQualification(
        driver_id=driver.id,
        company_id=current_user.company_id,
        qualification_type=payload.qualification_type,
        license_class=payload.license_class,
        certificate_number=payload.certificate_number,
        issuing_authority=payload.issuing_authority,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        evidence_url=payload.evidence_url,
        verification_status=QualificationVerificationStatus.PENDING,
    )
    db.add(qual)
    await db.commit()
    await db.refresh(qual)
    return DriverQualificationResponse.model_validate(qual)


@router.get("/drivers/{driver_id}/qualifications", response_model=List[DriverQualificationResponse])
async def list_driver_qualifications(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DriverQualificationResponse]:
    """
    List all qualifications for a driver within the tenant.
    """
    driver = await db.get(Driver, driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Driver not found")

    stmt = select(DriverQualification).where(
        DriverQualification.driver_id == driver.id,
        DriverQualification.company_id == current_user.company_id,
    ).order_by(DriverQualification.created_at.desc())

    result = await db.execute(stmt)
    quals = result.scalars().all()
    return [DriverQualificationResponse.model_validate(q) for q in quals]


@router.get("/driver-qualifications/{qualification_id}", response_model=DriverQualificationResponse)
async def get_driver_qualification(
    qualification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverQualificationResponse:
    """
    Get a single qualification by ID.
    """
    qual = await db.get(DriverQualification, qualification_id)
    if not qual or qual.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Qualification not found")

    return DriverQualificationResponse.model_validate(qual)


@router.patch("/driver-qualifications/{qualification_id}", response_model=DriverQualificationResponse)
async def update_driver_qualification(
    qualification_id: int,
    payload: DriverQualificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverQualificationResponse:
    """
    Update qualification metadata.
    """
    qual = await db.get(DriverQualification, qualification_id)
    if not qual or qual.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Qualification not found")

    if payload.qualification_type is not None:
        qual.qualification_type = payload.qualification_type
    if payload.license_class is not None:
        qual.license_class = payload.license_class
    if payload.certificate_number is not None:
        qual.certificate_number = payload.certificate_number
    if payload.issuing_authority is not None:
        qual.issuing_authority = payload.issuing_authority
    if payload.issue_date is not None:
        qual.issue_date = payload.issue_date
    if payload.expiry_date is not None:
        qual.expiry_date = payload.expiry_date
    if payload.evidence_url is not None:
        qual.evidence_url = payload.evidence_url

    await db.commit()
    await db.refresh(qual)
    return DriverQualificationResponse.model_validate(qual)


@router.post("/driver-qualifications/{qualification_id}/verify", response_model=DriverQualificationResponse)
async def verify_driver_qualification(
    qualification_id: int,
    payload: DriverQualificationVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverQualificationResponse:
    """
    Authorize or reject a driver qualification.
    Strict RBAC: Only COMPANY_ADMIN, FLEET_MANAGER, ADMIN, or SUPER_ADMIN can verify.
    Drivers are strictly forbidden.
    """
    if current_user.role not in VERIFICATION_PERMITTED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack authorized administrative role to verify or reject driver qualifications."
        )

    qual = await db.get(DriverQualification, qualification_id)
    if not qual or qual.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Qualification not found")

    if payload.verification_status not in [QualificationVerificationStatus.VERIFIED, QualificationVerificationStatus.REJECTED]:
        raise HTTPException(status_code=400, detail="Decision must be VERIFIED or REJECTED")

    qual.verification_status = payload.verification_status
    qual.verified_by = getattr(current_user, "email", None) or str(current_user.id)
    qual.verified_at = datetime.now(timezone.utc)
    if payload.verification_status == QualificationVerificationStatus.REJECTED:
        qual.rejection_reason = payload.rejection_reason
    else:
        qual.rejection_reason = None

    await db.commit()
    await db.refresh(qual)
    return DriverQualificationResponse.model_validate(qual)


@router.delete("/driver-qualifications/{qualification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver_qualification(
    qualification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Revoke/delete a driver qualification.
    """
    if current_user.role not in VERIFICATION_PERMITTED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack authorized administrative role to delete driver qualifications."
        )

    qual = await db.get(DriverQualification, qualification_id)
    if not qual or qual.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Qualification not found")

    await db.delete(qual)
    await db.commit()
    return None
