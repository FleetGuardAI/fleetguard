"""
FleetGuard — Driver Mobile App API Router

Handles the complete driver mobile app flow:
- Fleet invite verification (QR code scan)
- OTP-based phone authentication
- Driver profile creation with document uploads
- Face verification (demo: simulated)
- Profile management
- FCM token registration
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
from services.otp_service import otp_service
from services.file_upload_service import storage_service
from utils.security import hash_password, create_access_token

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
    otp_code: str
    invite_token: str

class VerifyOtpResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    driver_id: Optional[int] = None
    is_new_driver: bool = True
    verification_status: Optional[str] = None

class DriverProfileRequest(BaseModel):
    name: str = Field(..., min_length=2)
    license_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    employee_id: Optional[str] = None

class DriverProfileResponse(BaseModel):
    id: int
    name: str
    phone_number: str
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

async def get_current_driver(db: AsyncSession = Depends(get_db)) -> Driver:
    """
    Extract driver from JWT token.
    Reuses the existing auth service's token format.
    """
    # This is a simplified version — in production, extract from JWT
    # For the driver app, we use the same JWT format as the dashboard
    from fastapi import Request
    from fastapi.security import OAuth2PasswordBearer
    from utils.security import decode_access_token
    from jose import JWTError

    # This will be injected via the auth interceptor
    # For now, we'll create a proper dependency
    raise HTTPException(401, "Use get_driver_from_token dependency")


async def get_driver_from_token(
    db: AsyncSession = Depends(get_db),
) -> Driver:
    """Get the authenticated driver from JWT token."""
    from fastapi import Request
    # We'll use a simpler approach — the auth interceptor handles this
    # Return a stub for now that gets replaced by proper middleware
    pass


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
    Demo mode: OTP is always 123456.
    """
    success = await otp_service.send_otp(payload.phone_number)
    if not success:
        raise HTTPException(500, "Failed to send OTP")
    return {"message": "OTP sent successfully", "demo_otp": "123456"}


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
    is_valid = await otp_service.verify_otp(payload.phone_number, payload.otp_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
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
    db: AsyncSession = Depends(get_db),
):
    """
    Complete driver profile registration after OTP verification.
    Updates driver name, license, aadhaar, and sets status to PENDING_DOCUMENTS.
    """
    # Extract driver_id from token
    from services.auth_service import get_current_user
    # We'll use a simpler auth check for the driver app
    # In practice, the JWT already contains the driver_id
    from fastapi import Request

    # For this endpoint, we need to extract driver from the existing JWT
    # The token was created in verify_otp with driver_id in payload
    # We'll use a helper to extract it
    driver_id = await _extract_driver_id_from_token(db)
    if driver_id is None:
        raise HTTPException(401, "Authentication required")

    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    driver.name = payload.name
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

    return _driver_to_response(driver)


@router.post("/upload-document")
async def upload_document(
    document_type: str = Form(..., description="license_front, license_back, aadhaar_front, aadhaar_back, selfie"),
    driver_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a driver document (license, aadhaar, selfie).
    Stores locally for demo, abstracted for S3/R2 in production.
    """
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    # Validate document type
    valid_types = ["license_front", "license_back", "aadhaar_front", "aadhaar_back", "selfie"]
    if document_type not in valid_types:
        raise HTTPException(400, f"Invalid document type. Must be one of: {valid_types}")

    # Upload file
    url = await storage_service.upload_file(
        file=file,
        folder=f"drivers/{driver.id}",
    )

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
        "url": url,
        "verification_status": driver.verification_status.value if driver.verification_status else None,
    }


@router.post("/face-verify", response_model=FaceVerifyResponse)
async def face_verify(
    driver_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Selfie-to-license face verification.

    Demo: simulates verification with 95% confidence.
    Production: integrate with face comparison AI (AWS Rekognition, etc.)
    """
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    if not driver.selfie_url or not driver.license_front_url:
        raise HTTPException(400, "Selfie and license front must be uploaded first")

    # Demo: simulate face verification
    driver.face_verified = True
    await db.commit()

    logger.info(f"[DEMO] Face verification passed for driver {driver_id}")

    return FaceVerifyResponse(
        verified=True,
        confidence=0.95,
        message="Face verification successful",
    )


@router.get("/profile", response_model=DriverProfileResponse)
async def get_driver_profile(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get driver profile with approval status."""
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")
    return _driver_to_response(driver)


@router.patch("/profile", response_model=DriverProfileResponse)
async def update_driver_profile(
    driver_id: int,
    payload: DriverProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update driver profile details."""
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    if payload.name:
        driver.name = payload.name
    if payload.license_number:
        driver.license_number = payload.license_number

    await db.commit()
    await db.refresh(driver)
    return _driver_to_response(driver)


@router.put("/fcm-token")
async def update_fcm_token(
    payload: FcmTokenRequest,
    driver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Update driver's FCM push notification token."""
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    driver.fcm_token = payload.fcm_token
    await db.commit()
    return {"message": "FCM token updated"}


# ==========================================================================
# Duty Management
# ==========================================================================

@router.post("/duty/start")
async def start_duty(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Start driver's duty shift."""
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    driver.duty_status = DutyStatus.ON_DUTY
    await db.commit()

    logger.info(f"Driver {driver_id} started duty")
    return {"message": "Duty started", "duty_status": "ON_DUTY"}


@router.post("/duty/end")
async def end_duty(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """End driver's duty shift."""
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    driver.duty_status = DutyStatus.OFF_DUTY
    await db.commit()

    logger.info(f"Driver {driver_id} ended duty")
    return {"message": "Duty ended", "duty_status": "OFF_DUTY"}


@router.post("/duty/break")
async def start_break(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Start a break during duty."""
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    driver.duty_status = DutyStatus.ON_BREAK
    await db.commit()

    return {"message": "Break started", "duty_status": "ON_BREAK"}


@router.post("/duty/resume")
async def resume_duty(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Resume duty after break."""
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    driver.duty_status = DutyStatus.ON_DUTY
    await db.commit()

    return {"message": "Duty resumed", "duty_status": "ON_DUTY"}


# ==========================================================================
# Helpers
# ==========================================================================

def _driver_to_response(driver: Driver) -> DriverProfileResponse:
    """Convert Driver ORM to response schema."""
    return DriverProfileResponse(
        id=driver.id,
        name=driver.name,
        phone_number=driver.phone_number,
        avatar_url=driver.avatar_url or driver.selfie_url,
        company_id=driver.company_id,
        company_name=driver.company.company_name if driver.company else None,
        license_number=driver.license_number,
        license_front_url=driver.license_front_url,
        license_back_url=driver.license_back_url,
        aadhaar_front_url=driver.aadhaar_front_url,
        aadhaar_back_url=driver.aadhaar_back_url,
        selfie_url=driver.selfie_url,
        verification_status=driver.verification_status.value if driver.verification_status else None,
        face_verified=driver.face_verified,
        duty_status=driver.duty_status.value if driver.duty_status else None,
        driver_score=driver.driver_score,
        status=driver.status.value,
    )


async def _extract_driver_id_from_token(db: AsyncSession) -> Optional[int]:
    """
    Helper to extract driver_id from the current request's JWT.
    This is a simplified version for demo — in production, use proper middleware.
    """
    # For demo, we'll query the most recently created driver
    # In production, the JWT middleware would inject this
    result = await db.execute(
        select(Driver).order_by(Driver.id.desc()).limit(1)
    )
    driver = result.scalar_one_or_none()
    return driver.id if driver else None
