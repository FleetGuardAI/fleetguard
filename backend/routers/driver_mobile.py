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
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from schemas.document import DocumentResponse

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

    # Check if driver already exists globally (phone_number is globally unique)
    driver_result = await db.execute(
        select(Driver).where(Driver.phone_number == payload.phone_number)
    )
    driver = driver_result.scalars().first()

    is_new = driver is None

    if is_new:
        disambiguated_phone = f"{payload.phone_number}_d{company_id}"

        # Check if user with this phone (or disambiguated) exists
        user_result = await db.execute(
            select(User).where(
                User.mobile_number.in_([payload.phone_number, disambiguated_phone])
            )
        )
        existing_users = user_result.scalars().all()
        user_map = {u.mobile_number: u for u in existing_users}

        user = None

        if disambiguated_phone in user_map:
            # We already have a disambiguated user for this company, reuse it
            user = user_map[disambiguated_phone]
        elif payload.phone_number in user_map:
            primary_user = user_map[payload.phone_number]
            if primary_user.company_id == company_id and primary_user.role == UserRole.DRIVER:
                # Same company, same role — reuse the primary user
                user = primary_user
            else:
                # Primary exists but is different company/role. Create disambiguated.
                user = User(
                    company_id=company_id,
                    full_name=payload.phone_number,
                    mobile_number=disambiguated_phone,
                    password_hash=hash_password(secrets.token_urlsafe(24)),
                    role=UserRole.DRIVER,
                    is_active=True,
                )
                db.add(user)
                try:
                    async with db.begin_nested():
                        await db.flush()
                except IntegrityError:
                    # It was created concurrently! Fetch it.
                    user_result = await db.execute(
                        select(User).where(User.mobile_number == disambiguated_phone)
                    )
                    user = user_result.scalar_one()
        else:
            # No user exists. Create primary user.
            user = User(
                company_id=company_id,
                full_name=payload.phone_number,
                mobile_number=payload.phone_number,
                password_hash=hash_password(secrets.token_urlsafe(24)),
                role=UserRole.DRIVER,
                is_active=True,
            )
            db.add(user)
            try:
                async with db.begin_nested():
                    await db.flush()
            except IntegrityError:
                user_result = await db.execute(
                    select(User).where(User.mobile_number == payload.phone_number)
                )
                user = user_result.scalar_one()

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
        try:
            async with db.begin_nested():
                await db.flush()
        except IntegrityError:
            # Driver was created concurrently
            driver_result = await db.execute(
                select(Driver).where(Driver.phone_number == payload.phone_number)
            )
            driver = driver_result.scalar_one()
    else:
        # Driver already exists. 
        # If they are joining a new company via invite, we should update their company_id
        # to the new company so they can operate under it, as phone_number is globally unique.
        if driver.company_id != company_id:
            driver.company_id = company_id
            
            # We must also ensure they use the correct user for this company.
            disambiguated_phone = f"{payload.phone_number}_d{company_id}"
            user_result = await db.execute(
                select(User).where(
                    User.mobile_number.in_([payload.phone_number, disambiguated_phone])
                )
            )
            existing_users = user_result.scalars().all()
            user_map = {u.mobile_number: u for u in existing_users}
            
            if disambiguated_phone in user_map:
                driver.user_id = user_map[disambiguated_phone].id
            elif payload.phone_number in user_map:
                primary = user_map[payload.phone_number]
                if primary.company_id == company_id:
                    driver.user_id = primary.id
                else:
                    # Create disambiguated user
                    user = User(
                        company_id=company_id,
                        full_name=payload.phone_number,
                        mobile_number=disambiguated_phone,
                        password_hash=hash_password(secrets.token_urlsafe(24)),
                        role=UserRole.DRIVER,
                        is_active=True,
                    )
                    db.add(user)
                    try:
                        async with db.begin_nested():
                            await db.flush()
                    except IntegrityError:
                        user_result = await db.execute(
                            select(User).where(User.mobile_number == disambiguated_phone)
                        )
                        user = user_result.scalar_one()
                    driver.user_id = user.id

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
    try:
        logger.info("[UPLOAD DEBUG] REQUEST START")
        logger.info("[UPLOAD DEBUG] authenticated user/driver resolved")
        logger.info(f"[UPLOAD DEBUG] document type: {document_type}")
        logger.info(f"[UPLOAD DEBUG] filename: {file.filename}")
        logger.info(f"[UPLOAD DEBUG] content type: {file.content_type}")
        logger.info(f"[UPLOAD DEBUG] file size: {getattr(file, 'size', 'unknown')}")
        logger.info("[UPLOAD DEBUG] database lookup completed")

        # Validate document type
        valid_types = ["license_front", "license_back", "aadhaar_front", "aadhaar_back", "selfie"]
        if document_type not in valid_types:
            raise HTTPException(400, f"Invalid document type. Must be one of: {valid_types}")

        from services.unified_pipeline_service import UnifiedPipelineService
        from models.operational_event import EntityType
        
        pipeline = UnifiedPipelineService(db)
        
        logger.info("[UPLOAD DEBUG] storage upload started")
        url, extracted_fields = await pipeline.process_document(
            file=file,
            document_type="idDocument", # Default ID processor for these docs
            entity_type=EntityType.DRIVER,
            entity_id=str(driver.id),
            uploaded_by=f"driver_{driver.id}",
            company_id=driver.company_id,
            category=document_type
        )
        logger.info("[UPLOAD DEBUG] storage upload completed")

        logger.info("[UPLOAD DEBUG] database insert/update started")
        # Update driver record
        setattr(driver, f"{document_type}_url", url)

        # Check driver verification status by looking at the latest document in each category
        from models.document import Document, DocumentVerificationStatus
        
        all_docs_result = await db.execute(
            select(Document)
            .where(Document.target_id == str(driver.id))
            .where(Document.target_type == "DRIVER")
            .order_by(desc(Document.created_at))
        )
        all_docs = all_docs_result.scalars().all()
        
        latest_by_category = {}
        for d in all_docs:
            if d.category and d.category not in latest_by_category:
                latest_by_category[d.category] = d
                
        required_categories = ["license_front", "license_back", "aadhaar_front", "aadhaar_back", "selfie"]
        
        all_required_approved = True
        any_latest_rejected = False
        has_all_required = True
        
        for cat in required_categories:
            latest_doc = latest_by_category.get(cat)
            if not latest_doc:
                has_all_required = False
                all_required_approved = False
                continue
            if latest_doc.verification_status != DocumentVerificationStatus.APPROVED:
                all_required_approved = False
            if latest_doc.verification_status == DocumentVerificationStatus.REJECTED:
                any_latest_rejected = True
                
        if has_all_required and all_required_approved:
            driver.verification_status = VerificationStatus.APPROVED
        elif any_latest_rejected:
            driver.verification_status = VerificationStatus.REJECTED
        elif has_all_required:
            driver.verification_status = VerificationStatus.PENDING_APPROVAL
        else:
            driver.verification_status = VerificationStatus.PENDING_DOCUMENTS

        await db.commit()
        await db.refresh(driver)
        logger.info("[UPLOAD DEBUG] database insert/update completed")

        result = {
            "message": f"{document_type} uploaded successfully",
            "url": storage_service.create_signed_url(url),
            "verification_status": driver.verification_status.value if driver.verification_status else None,
            "extracted_fields": extracted_fields
        }
        logger.info("[UPLOAD DEBUG] RESPONSE SUCCESS")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[UPLOAD DEBUG] EXCEPTION\nexception class: {e.__class__.__name__}\nexception message: {str(e)}")
        raise HTTPException(500, "Failed to upload and process document")

@router.get("/documents", response_model=list[DocumentResponse])
async def get_my_documents(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the latest documents for each category for the current driver.
    Provides document status and rejection reasons if any.
    """
    from models.document import Document
    from services.file_upload_service import storage_service
    
    result = await db.execute(
        select(Document)
        .where(Document.target_id == str(driver.id))
        .where(Document.target_type == "DRIVER")
        .order_by(desc(Document.created_at))
    )
    all_docs = result.scalars().all()
    
    # Only return the latest document per category
    latest_by_category = {}
    for d in all_docs:
        if d.category and d.category not in latest_by_category:
            latest_by_category[d.category] = d
            
    results = []
    for doc in latest_by_category.values():
        resp = DocumentResponse.model_validate(doc)
        resp.storage_path = storage_service.create_signed_url(doc.storage_path)
        results.append(resp)
        
    return results



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
