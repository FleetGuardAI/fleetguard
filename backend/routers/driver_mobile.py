"""
FleetGuard — Driver Mobile App API Router

Handles the complete driver mobile app flow:
- Fleet invite verification (QR code scan)
- OTP-based phone authentication
- Driver profile creation with document uploads
- Face verification (demo: simulated)
- Profile management
- FCM token registration
- Duty management

Security:
All endpoints (except OTP/invite verification) require a valid JWT token.
The `get_current_driver` dependency ensures the authenticated user is actually a driver
and retrieves their driver profile.
This prevents IDOR (Insecure Direct Object Reference) by not accepting `driver_id` from the client.
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User, UserRole
from models.driver_domain import Driver, DriverStatus, VerificationStatus, DutyStatus
from models.fleet_invite import FleetInvite
from config import settings
from services.otp_service import get_otp_provider
from services.file_upload_service import storage_service
from utils.security import hash_password, create_access_token
from services.auth_service import get_current_user

logger = logging.getLogger("fleetguard.driver_mobile")

router = APIRouter(prefix="/api/v1/driver-app", tags=["Driver Mobile App"])


# ==========================================================================
# Request / Response Schemas
# ==========================================================================

class VerifyInviteRequest(BaseModel):
    invite_token: str = Field(..., description="Token from QR code scan")

class VerifyInviteResponse(BaseModel):
    valid: bool
    company_name: str = ""
    company_id: int = 0

class SendOtpRequest(BaseModel):
    phone_number: str = Field(..., min_length=10)

class VerifyOtpRequest(BaseModel):
    phone_number: str
    req_id: str
    otp_code: str
    invite_token: str
    msg91_token: Optional[str] = None

class VerifyOtpResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    driver_id: Optional[int] = None
    is_new_driver: bool = True
    verification_status: Optional[str] = None

class DriverProfileRequest(BaseModel):
    name: str = Field(..., min_length=2)
    age: Optional[int] = Field(None, ge=18, le=80)
    license_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    employee_id: Optional[str] = None

class DriverProfileResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    age: Optional[int] = None
    avatar_url: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    license_number: Optional[str] = None
    license_front_url: Optional[str] = None
    license_back_url: Optional[str] = None
    aadhaar_front_url: Optional[str] = None
    aadhaar_back_url: Optional[str] = None
    selfie_url: Optional[str] = None
    verification_status: Optional[str] = None
    face_verified: Optional[bool] = None
    duty_status: Optional[str] = None
    driver_score: Optional[float] = None
    status: str
    assigned_vehicle: Optional[str] = None

    model_config = {"from_attributes": True}

class FaceVerifyResponse(BaseModel):
    verified: bool
    confidence: float
    message: str

class FcmTokenRequest(BaseModel):
    fcm_token: str


# ==========================================================================
# Dependencies
# ==========================================================================

async def get_current_driver(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Driver:
    """
    Get the authenticated driver profile.
    Prevents IDOR by using the trusted JWT token to look up the driver.
    """
    result = await db.execute(
        select(Driver).where(Driver.user_id == current_user.id)
    )
    driver = result.scalar_one_or_none()
    
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is not registered as a driver"
        )
    return driver


# ==========================================================================
# Auth Endpoints
# ==========================================================================

@router.post("/verify-invite", response_model=VerifyInviteResponse)
async def verify_invite(
    payload: VerifyInviteRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyInviteResponse:
    """
    Verify a fleet invite token from QR code scan.
    Returns company info if the invite is valid.
    """
    result = await db.execute(
        select(FleetInvite).where(FleetInvite.invite_token == payload.invite_token)
    )
    invite = result.scalar_one_or_none()

    if invite is None or not invite.is_valid:
        return VerifyInviteResponse(valid=False)

    company = invite.company
    return VerifyInviteResponse(
        valid=True,
        company_name=company.company_name if company else "Unknown",
        company_id=invite.company_id,
    )


@router.post("/send-otp")
async def send_otp(payload: SendOtpRequest):
    """
    Send OTP to driver's phone number.
    """
    otp_provider = get_otp_provider()
    result = await otp_provider.request_otp(payload.phone_number)
    if not result.success:
        raise HTTPException(500, result.message)
    return {
        "message": result.message,
        "req_id": result.provider_reference,
        "demo_otp": "123456" if getattr(settings, 'OTP_MOCK_MODE', False) else None
    }


@router.post("/verify-otp", response_model=VerifyOtpResponse)
async def verify_otp(
    payload: VerifyOtpRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyOtpResponse:
    """
    Verify OTP and authenticate/register driver.

    - If driver exists: log them in.
    - If driver is new: create User + Driver records.
    """
    # Verify OTP
    otp_provider = get_otp_provider()
    
    if payload.msg91_token:
        result = await otp_provider.verify_access_token(payload.msg91_token)
    else:
        result = await otp_provider.verify_otp(payload.req_id, payload.otp_code)
        
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    # Validate invite token
    invite_result = await db.execute(
        select(FleetInvite).where(FleetInvite.invite_token == payload.invite_token)
    )
    invite = invite_result.scalar_one_or_none()
    if invite is None or not invite.is_valid:
        raise HTTPException(400, "Invalid or expired invite")

    company_id = invite.company_id

    # Check if driver already exists
    driver_result = await db.execute(
        select(Driver).where(Driver.phone_number == payload.phone_number)
    )
    driver = driver_result.scalar_one_or_none()

    is_new = driver is None

    if is_new:
        # Check if user with this phone exists
        user_result = await db.execute(
            select(User).where(User.mobile_number == payload.phone_number)
        )
        user = user_result.scalar_one_or_none()

        if user is None:
            # Create new user with DRIVER role
            user = User(
                company_id=company_id,
                full_name=payload.phone_number,  # Will be updated during profile creation
                mobile_number=payload.phone_number,
                password_hash=hash_password(secrets.token_urlsafe(24)),  # Random password
                role=UserRole.DRIVER,
                is_active=True,
            )
            db.add(user)
            await db.flush()
        elif user.company_id == company_id and user.role == UserRole.DRIVER:
            # Same company, same role — reuse the user as-is
            pass
        else:
            # User exists but belongs to a different company or has a non-DRIVER role
            # (e.g., they are COMPANY_ADMIN for another tenant).
            # We must NOT overwrite their company_id/role — create a fresh DRIVER user.
            logger.info(
                f"[DRIVER ONBOARD] Existing user {user.id} has role={user.role}, "
                f"company_id={user.company_id}. Creating new DRIVER user for company {company_id}."
            )
            user = User(
                company_id=company_id,
                full_name=payload.phone_number,
                mobile_number=f"{payload.phone_number}_d{company_id}",  # disambiguate
                password_hash=hash_password(secrets.token_urlsafe(24)),
                role=UserRole.DRIVER,
                is_active=True,
            )
            db.add(user)
            await db.flush()

        # Create new driver
        driver = Driver(
            name=payload.phone_number,  # Will be updated during profile creation
            phone_number=payload.phone_number,
            company_id=company_id,
            user_id=user.id,
            status=DriverStatus.ACTIVE,
            verification_status=VerificationStatus.PENDING_DOCUMENTS,
            origin_type="driver_app",
        )
        db.add(driver)
        await db.flush()

        # Increment invite usage
        invite.use_count += 1

    # Generate JWT token
    from models.auth_session import AuthSession

    jti = secrets.token_urlsafe(24)
    session = AuthSession(
        user_id=driver.user_id or 0,
        company_id=company_id,
        session_jti=jti,
        remember_me=True,
        expires_at=datetime.now(tz=timezone.utc) + __import__('datetime').timedelta(days=30),
    )
    db.add(session)

    token = create_access_token(
        data={
            "sub": str(driver.user_id),
            "company_id": company_id,
            "role": UserRole.DRIVER.value,
            "driver_id": driver.id,
            "jti": jti,
            "remember_me": True,
        }
    )

    await db.commit()

    return VerifyOtpResponse(
        access_token=token,
        driver_id=driver.id,
        is_new_driver=is_new,
        verification_status=driver.verification_status.value if driver.verification_status else None,
    )


# ==========================================================================
# Profile Endpoints
# ==========================================================================

@router.post("/register", response_model=DriverProfileResponse)
async def register_driver_profile(
    payload: DriverProfileRequest,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete driver profile registration after OTP verification.
    Updates driver name, license, aadhaar, and sets status to PENDING_DOCUMENTS.
    """
    driver.name = payload.name
    if payload.age:
        driver.age = payload.age
    if payload.license_number:
        driver.license_number = payload.license_number
    if payload.aadhaar_number:
        driver.aadhaar_number = payload.aadhaar_number
    if payload.employee_id:
        driver.employee_id = payload.employee_id

    # Update linked user name
    if driver.user_id:
        user = await db.get(User, driver.user_id)
        if user:
            user.full_name = payload.name

    driver.verification_status = VerificationStatus.PENDING_DOCUMENTS

    await db.commit()
    await db.refresh(driver)

    response = _driver_to_response(driver)
    response.assigned_vehicle = await _get_assigned_vehicle(driver.id, db)
    return response


@router.post("/upload-document")
async def upload_document(
    document_type: str = Form(..., description="license_front, license_back, aadhaar_front, aadhaar_back, selfie"),
    file: UploadFile = File(...),
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a driver document (license, aadhaar, selfie).
    Uses the unified document pipeline to upload, OCR, and store metadata.
    """
    # Validate document type
    valid_types = ["license_front", "license_back", "aadhaar_front", "aadhaar_back", "selfie"]
    if document_type not in valid_types:
        raise HTTPException(400, f"Invalid document type. Must be one of: {valid_types}")

    from services.unified_pipeline_service import UnifiedPipelineService
    from models.operational_event import EntityType
    
    pipeline = UnifiedPipelineService(db)
    
    try:
        url, extracted_fields = await pipeline.process_document(
            file=file,
            document_type="idDocument", # Default ID processor for these docs
            entity_type=EntityType.DRIVER,
            entity_id=str(driver.id),
            uploaded_by=f"driver_{driver.id}",
            company_id=driver.company_id
        )
    except Exception as e:
        logger.error(f"Failed to process document upload: {e}")
        raise HTTPException(500, "Failed to upload and process document")

    # Update driver record
    setattr(driver, f"{document_type}_url", url)

    # Check if all documents are uploaded
    has_all_docs = all([
        driver.license_front_url,
        driver.license_back_url,
        driver.aadhaar_front_url,
        driver.aadhaar_back_url,
        driver.selfie_url,
    ])

    if has_all_docs and driver.verification_status == VerificationStatus.PENDING_DOCUMENTS:
        driver.verification_status = VerificationStatus.PENDING_APPROVAL

    await db.commit()
    await db.refresh(driver)

    return {
        "message": f"{document_type} uploaded successfully",
        "url": storage_service.create_signed_url(url),
        "verification_status": driver.verification_status.value if driver.verification_status else None,
        "extracted_fields": extracted_fields
    }


@router.post("/face-verify", response_model=FaceVerifyResponse)
async def face_verify(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Selfie-to-license face verification.

    Demo: simulates verification with 95% confidence.
    Production: integrate with face comparison AI (AWS Rekognition, etc.)
    """
    if not driver.selfie_url or not driver.license_front_url:
        raise HTTPException(400, "Selfie and license front must be uploaded first")

    # Demo: simulate face verification
    driver.face_verified = True
    await db.commit()

    logger.info(f"[DEMO] Face verification passed for driver {driver.id}")

    return FaceVerifyResponse(
        verified=True,
        confidence=0.95,
        message="Face verification successful",
    )


@router.get("/profile", response_model=DriverProfileResponse)
async def get_driver_profile(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Get driver profile with approval status."""
    response = _driver_to_response(driver)
    response.assigned_vehicle = await _get_assigned_vehicle(driver.id, db)
    return response


@router.patch("/profile", response_model=DriverProfileResponse)
async def update_driver_profile(
    payload: DriverProfileRequest,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Update driver profile details."""
    if payload.name:
        driver.name = payload.name
    if payload.license_number:
        driver.license_number = payload.license_number

    await db.commit()
    await db.refresh(driver)
    response = _driver_to_response(driver)
    response.assigned_vehicle = await _get_assigned_vehicle(driver.id, db)
    return response


@router.put("/fcm-token")
async def update_fcm_token(
    payload: FcmTokenRequest,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Update driver's FCM push notification token."""
    driver.fcm_token = payload.fcm_token
    await db.commit()
    return {"message": "FCM token updated"}


# ==========================================================================
# Duty Management
# ==========================================================================

@router.post("/duty/start")
async def start_duty(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Start driver's duty shift."""
    driver.duty_status = DutyStatus.ON_DUTY
    await db.commit()

    logger.info(f"Driver {driver.id} started duty")
    return {"message": "Duty started", "duty_status": "ON_DUTY"}


@router.post("/duty/end")
async def end_duty(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """End driver's duty shift."""
    driver.duty_status = DutyStatus.OFF_DUTY
    await db.commit()

    logger.info(f"Driver {driver.id} ended duty")
    return {"message": "Duty ended", "duty_status": "OFF_DUTY"}


@router.post("/duty/break")
async def start_break(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Start a break during duty."""
    driver.duty_status = DutyStatus.ON_BREAK
    await db.commit()

    return {"message": "Break started", "duty_status": "ON_BREAK"}


@router.post("/duty/resume")
async def resume_duty(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Resume duty after break."""
    driver.duty_status = DutyStatus.ON_DUTY
    await db.commit()

    return {"message": "Duty resumed", "duty_status": "ON_DUTY"}


# ==========================================================================
# Helpers
# ==========================================================================

def _driver_to_response(driver: Driver) -> DriverProfileResponse:
    """Convert Driver ORM to response schema, resolving signed URLs."""
    from services.file_upload_service import storage_service
    
    return DriverProfileResponse(
        id=driver.id,
        name=driver.name,
        phone_number=driver.phone_number,
        age=driver.age,
        avatar_url=storage_service.create_signed_url(driver.avatar_url or driver.selfie_url),
        company_id=driver.company_id,
        company_name=driver.company.company_name if driver.company else None,
        license_number=driver.license_number,
        license_front_url=storage_service.create_signed_url(driver.license_front_url),
        license_back_url=storage_service.create_signed_url(driver.license_back_url),
        aadhaar_front_url=storage_service.create_signed_url(driver.aadhaar_front_url),
        aadhaar_back_url=storage_service.create_signed_url(driver.aadhaar_back_url),
        selfie_url=storage_service.create_signed_url(driver.selfie_url),
        verification_status=driver.verification_status.value if driver.verification_status else None,
        face_verified=driver.face_verified,
        duty_status=driver.duty_status.value if driver.duty_status else None,
        driver_score=driver.driver_score,
        status=driver.status.value,
        assigned_vehicle=None, # Populated below if vehicle is passed or queried
    )

async def _get_assigned_vehicle(driver_id: int, db: AsyncSession) -> Optional[str]:
    """Helper to get registration number of currently assigned vehicle."""
    from sqlalchemy import select
    from models.vehicle_domain import Vehicle
    result = await db.execute(
        select(Vehicle).where(Vehicle.assigned_driver_id == driver_id).limit(1)
    )
    vehicle = result.scalar_one_or_none()
    return vehicle.registration_number if vehicle else None
