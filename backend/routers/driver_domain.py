"""
FleetGuard — Driver Domain API Router
Provides REST APIs for Driver Business Domain CRUD operations.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from services.driver_service import DriverService
from models.driver_domain import Driver, DriverStatus
from models.vehicle_domain import Vehicle
from models.operational_event import OperationalEvent, EventType, EntityType, CaptureMethod
from schemas.driver_domain import DriverResponse, DriverCreate, DriverUpdated
from services.auth_service import get_current_user
from models.user import User, UserRole

router = APIRouter(prefix="/v1", tags=["Driver Domain"])


@router.get("/drivers", response_model=List[DriverResponse])
async def list_drivers(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> List[DriverResponse]:
    """List all drivers with optional active filter."""
    service = DriverService(uow)
    drivers = await service.search_drivers(is_active=is_active, limit=limit, offset=offset, company_id=current_user.company_id)
    
    # Enrich with assigned vehicle registration numbers
    results = []
    for d in drivers:
        resp = DriverResponse.model_validate(d)
        # assigned_vehicle from vehicle table
        session = getattr(uow, 'session', getattr(uow, '_session', None))
        v_result = await session.execute(
            select(Vehicle.registration_number).where(Vehicle.assigned_driver_id == d.id).limit(1)
        )
        reg = v_result.scalar_one_or_none()
        resp.assigned_vehicle = reg
        results.append(resp)
    return results


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: int, 
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> DriverResponse:
    """Get a single driver by ID."""
    service = DriverService(uow)
    driver = await service.get_driver(driver_id, company_id=current_user.company_id)
    if not driver:
        raise HTTPException(404, f"Driver {driver_id} not found")
    resp = DriverResponse.model_validate(driver)
    # Enrich with assigned vehicle
    session = getattr(uow, 'session', getattr(uow, '_session', None))
    v_result = await session.execute(
        select(Vehicle.registration_number).where(Vehicle.assigned_driver_id == driver.id).limit(1)
    )
    resp.assigned_vehicle = v_result.scalar_one_or_none()
    return resp


@router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    payload: DriverCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DriverResponse:
    """Register a new driver in the database."""
    # Check if driver with phone already exists
    existing = await db.execute(select(Driver).where(Driver.phone_number == payload.phone_number))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver with phone number {payload.phone_number} is already registered."
        )

    driver = Driver(
        name=payload.name,
        phone_number=payload.phone_number,
        avatar_url=payload.avatar_url,
        employee_id=payload.employee_id,
        license_number=payload.license_number,
        status=DriverStatus.ACTIVE,
        origin_type="rest_api",
        company_id=current_user.company_id
    )
    db.add(driver)
    await db.commit()
    await db.refresh(driver)

    # Log operational event for auditability
    event = OperationalEvent(
        event_type=EventType.DRIVER_REGISTERED,
        entity_type=EntityType.DRIVER,
        entity_id=driver.phone_number,
        company_id=current_user.company_id,
        occurred_at=datetime.now(timezone.utc),
        capture_method=CaptureMethod.API_INTEGRATION,
        payload={"name": driver.name, "phone_number": driver.phone_number},
    )
    db.add(event)
    await db.commit()

    return DriverResponse.model_validate(driver)


@router.patch("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: int,
    payload: DriverUpdated,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DriverResponse:
    """Update driver profile details."""
    driver = await db.get(Driver, driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(404, f"Driver {driver_id} not found")

    if payload.name is not None:
        driver.name = payload.name
    if payload.phone_number is not None:
        driver.phone_number = payload.phone_number
    if payload.avatar_url is not None:
        driver.avatar_url = payload.avatar_url

    await db.commit()
    await db.refresh(driver)
    return DriverResponse.model_validate(driver)


@router.delete("/drivers/{driver_id}", status_code=status.HTTP_200_OK)
async def delete_driver(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive/delete a driver."""
    driver = await db.get(Driver, driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(404, f"Driver {driver_id} not found")

    await db.delete(driver)
    await db.commit()
    return {"message": f"Driver {driver_id} deleted successfully"}


class DriverApprovalRequest(BaseModel):
    action: str = Field(..., description="APPROVED or REJECTED")
    reason: Optional[str] = Field(None, description="Required if action is REJECTED")


@router.post("/drivers/{driver_id}/approve", response_model=DriverResponse)
async def approve_driver(
    driver_id: int,
    payload: DriverApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverResponse:
    """
    Approve or reject a driver's account after document verification.

    Requires COMPANY_ADMIN or SUPER_ADMIN role. Enforces company ownership.

    For APPROVED:
    - All 5 required document categories must have latest doc with verification_status=APPROVED
    - Sets driver.verification_status=APPROVED, driver.status=ACTIVE
    - Activates linked User (is_active=True)
    - Creates a SYSTEM notification for the driver

    For REJECTED:
    - Sets driver.verification_status=REJECTED
    - Keeps driver and user inactive
    - Creates a SYSTEM notification for the driver with rejection reason
    """
    from models.driver_domain import VerificationStatus
    from models.document import Document, DocumentVerificationStatus
    from models.notification import Notification, NotificationCategory
    from pydantic import BaseModel as PydanticBaseModel

    # Role check
    if current_user.role not in [UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can approve or reject drivers")

    if payload.action not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="Action must be 'APPROVED' or 'REJECTED'")

    if payload.action == "REJECTED" and not payload.reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required")

    # Fetch driver with company check
    driver = await db.get(Driver, driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found")

    if payload.action == "APPROVED":
        # Verify all 5 required document categories are present and approved
        all_docs_result = await db.execute(
            select(Document)
            .where(Document.target_id == str(driver_id))
            .where(Document.target_type == "DRIVER")
            .where(Document.company_id == current_user.company_id)
            .order_by(Document.created_at.desc())
        )
        all_docs = all_docs_result.scalars().all()

        latest_by_category = {}
        for d in all_docs:
            if d.category and d.category not in latest_by_category:
                latest_by_category[d.category] = d

        required_categories = ["license_front", "license_back", "aadhaar_front", "aadhaar_back", "selfie"]
        missing = []
        not_approved = []
        for cat in required_categories:
            latest_doc = latest_by_category.get(cat)
            if not latest_doc:
                missing.append(cat)
            elif latest_doc.verification_status != DocumentVerificationStatus.APPROVED:
                not_approved.append(cat)

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve: missing required documents: {', '.join(missing)}"
            )
        if not_approved:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve: documents not yet approved: {', '.join(not_approved)}"
            )

        # Approve driver
        driver.verification_status = VerificationStatus.APPROVED
        driver.status = DriverStatus.ACTIVE

        # Activate linked user
        if driver.user_id:
            user = await db.get(User, driver.user_id)
            if user:
                user.is_active = True

            # Create approval notification
            notification = Notification(
                category=NotificationCategory.SYSTEM,
                title="Driver Account Approved",
                description="Your driver account has been approved. You can now use the FleetGuard driver app.",
                company_id=current_user.company_id,
                user_id=driver.user_id,
            )
            db.add(notification)

    else:
        # Reject driver
        driver.verification_status = VerificationStatus.REJECTED
        # Keep driver inactive
        driver.status = DriverStatus.INACTIVE

        # Keep linked user inactive
        if driver.user_id:
            user = await db.get(User, driver.user_id)
            if user:
                user.is_active = False

            # Create rejection notification
            notification = Notification(
                category=NotificationCategory.SYSTEM,
                title="Driver Account Rejected",
                description=f"Your driver account has been rejected. Reason: {payload.reason}",
                company_id=current_user.company_id,
                user_id=driver.user_id,
            )
            db.add(notification)

    await db.commit()
    await db.refresh(driver)

    resp = DriverResponse.model_validate(driver)
    # Enrich with assigned vehicle
    v_result = await db.execute(
        select(Vehicle.registration_number).where(Vehicle.assigned_driver_id == driver.id).limit(1)
    )
    resp.assigned_vehicle = v_result.scalar_one_or_none()
    return resp
