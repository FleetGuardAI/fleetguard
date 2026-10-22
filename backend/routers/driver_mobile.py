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
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, parse_qs

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header, status
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from schemas.document import DocumentResponse

from database import get_db
from models.user import User, UserRole
from models.driver_domain import Driver, DriverStatus, VerificationStatus, DutyStatus
from models.company import Company, CompanyStatus
from models.fleet_invite import FleetInvite
from models.driver_fleet_transfer import DriverFleetTransfer, TransferStatus
from models.notification import Notification, NotificationCategory
from config import settings
from services.otp_service import get_otp_provider
from services.file_upload_service import storage_service
from utils.security import hash_password, create_access_token, decode_access_token
from services.auth_service import get_current_user_allow_inactive, get_current_user

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

class ResolveQrRequest(BaseModel):
    qr_data: str = Field(..., description="Raw QR code string or invite token")
    phone_number: Optional[str] = Field(None, description="Optional driver phone number")

class ResolveQrResponse(BaseModel):
    valid: bool
    action: str  # "LOGIN", "CONFIRM_SWITCH", "VERIFY_PHONE", "PENDING_DOCUMENTS", "PENDING_APPROVAL", "TRANSFER_PENDING", "BLOCKED", "INVALID"
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    invite_token: Optional[str] = None
    is_same_fleet: bool = False
    is_fleet_mismatch: bool = False
    current_company_id: Optional[int] = None
    current_company_name: Optional[str] = None
    target_company_id: Optional[int] = None
    target_company_name: Optional[str] = None
    driver_status: Optional[str] = None
    verification_status: Optional[str] = None
    has_pending_transfer: bool = False
    message: Optional[str] = None

class CreateFleetTransferRequest(BaseModel):
    invite_token: str
    target_company_id: int

class FleetTransferResponse(BaseModel):
    id: int
    driver_id: int
    from_company_id: int
    from_company_name: str
    to_company_id: int
    to_company_name: str
    status: str
    created_at: datetime
    message: str

class SendOtpRequest(BaseModel):
    phone_number: str = Field(..., min_length=10)

class VerifyOtpRequest(BaseModel):
    phone_number: str
    req_id: str
    otp_code: str
    invite_token: Optional[str] = None
    msg91_token: Optional[str] = None

class VerifyOtpResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    driver_id: Optional[int] = None
    is_new_driver: bool = True
    verification_status: Optional[str] = None
    driver_status: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    is_fleet_mismatch: bool = False
    current_company_id: Optional[int] = None
    current_company_name: Optional[str] = None
    target_company_id: Optional[int] = None
    target_company_name: Optional[str] = None
    has_pending_transfer: bool = False
    message: Optional[str] = None

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
    pending_transfer: Optional[Dict[str, Any]] = None

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

async def get_onboarding_driver(
    current_user: User = Depends(get_current_user_allow_inactive),
    db: AsyncSession = Depends(get_db)
) -> Driver:
    """
    Get the authenticated driver profile for onboarding ONLY.
    Allows access even if user/driver is inactive.
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

async def get_current_driver(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Driver:
    """
    Get the authenticated driver profile for normal operations.
    Enforces that User is active AND Driver is active.
    """
    result = await db.execute(
        select(Driver).where(Driver.user_id == current_user.id)
    )
    driver = result.scalar_one_or_none()
    
    if not driver or driver.status != DriverStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is not an active driver"
        )
    return driver


# ==========================================================================
# Auth Endpoints
# ==========================================================================

def parse_qr_token(qr_data: str) -> str:
    """Extract token string from raw QR content (URL, URI, JSON, or plain token)."""
    raw = qr_data.strip()
    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            if "token" in data:
                return data["token"]
            if "invite_token" in data:
                return data["invite_token"]
        except Exception:
            pass
    if "token=" in raw:
        parsed = urlparse(raw)
        qs = parse_qs(parsed.query)
        if "token" in qs and qs["token"]:
            return qs["token"][0]
    return raw


async def get_optional_driver(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[Driver]:
    """Extract authenticated driver if a valid Bearer token is provided."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", 0))
        if not user_id:
            return None
        result = await db.execute(select(Driver).where(Driver.user_id == user_id))
        return result.scalar_one_or_none()
    except Exception:
        return None


async def find_driver_by_phone(phone: str, db: AsyncSession) -> Optional[Driver]:
    """Find a driver record by phone number supporting normalized variants."""
    cleaned = "".join(ch for ch in phone if ch.isdigit())
    candidates = {phone, cleaned}
    if len(cleaned) >= 10:
        last10 = cleaned[-10:]
        candidates.update([last10, f"+91{last10}", f"91{last10}"])
    result = await db.execute(
        select(Driver).where(Driver.phone_number.in_(list(candidates)))
    )
    return result.scalars().first()


@router.post("/verify-invite", response_model=VerifyInviteResponse)
async def verify_invite(
    payload: VerifyInviteRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyInviteResponse:
    """
    Verify a fleet invite token from QR code scan.
    Returns company info if the invite is valid.
    """
    token = parse_qr_token(payload.invite_token)
    result = await db.execute(
        select(FleetInvite).where(FleetInvite.invite_token == token)
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


@router.post("/qr/resolve", response_model=ResolveQrResponse)
async def resolve_qr_code(
    payload: ResolveQrRequest,
    db: AsyncSession = Depends(get_db),
    auth_driver: Optional[Driver] = Depends(get_optional_driver),
) -> ResolveQrResponse:
    """
    Validate and resolve a fleet QR credential.
    Identifies the fleet, checks validity, and determines driver assignment relation:
    - Same fleet & approved -> LOGIN
    - Different fleet -> CONFIRM_SWITCH (fleet mismatch)
    - Unauthenticated -> VERIFY_PHONE
    """
    token = parse_qr_token(payload.qr_data)
    result = await db.execute(
        select(FleetInvite).where(FleetInvite.invite_token == token)
    )
    invite = result.scalar_one_or_none()

    if invite is None or not invite.is_valid:
        return ResolveQrResponse(
            valid=False,
            action="INVALID",
            message="Invalid, expired, or revoked fleet QR code."
        )

    company = invite.company
    if company is None or company.status != CompanyStatus.ACTIVE:
        return ResolveQrResponse(
            valid=False,
            action="INVALID",
            message="The fleet associated with this QR code is inactive."
        )

    # Resolve driver: from authenticated session or phone number if supplied
    driver = auth_driver
    if driver is None and payload.phone_number:
        driver = await find_driver_by_phone(payload.phone_number, db)

    # Case 1: Driver is identified
    if driver is not None:
        # Check if driver belongs to the scanned fleet
        if driver.company_id == invite.company_id:
            action = "LOGIN"
            if driver.verification_status == VerificationStatus.PENDING_DOCUMENTS:
                action = "PENDING_DOCUMENTS"
            elif driver.verification_status == VerificationStatus.PENDING_APPROVAL:
                action = "PENDING_APPROVAL"
            elif driver.status == DriverStatus.SUSPENDED:
                action = "BLOCKED"

            return ResolveQrResponse(
                valid=True,
                action=action,
                company_id=invite.company_id,
                company_name=company.company_name,
                invite_token=invite.invite_token,
                is_same_fleet=True,
                is_fleet_mismatch=False,
                current_company_id=driver.company_id,
                current_company_name=company.company_name,
                target_company_id=invite.company_id,
                target_company_name=company.company_name,
                driver_status=driver.status.value,
                verification_status=driver.verification_status.value if driver.verification_status else None,
                message="Driver already belongs to this fleet."
            )
        else:
            # Case 2: Driver belongs to a different fleet (Fleet Mismatch)
            transfer_res = await db.execute(
                select(DriverFleetTransfer)
                .where(
                    DriverFleetTransfer.driver_id == driver.id,
                    DriverFleetTransfer.to_company_id == invite.company_id,
                    DriverFleetTransfer.status == TransferStatus.PENDING_APPROVAL
                )
            )
            pending_transfer = transfer_res.scalars().first()

            current_comp = driver.company
            return ResolveQrResponse(
                valid=True,
                action="TRANSFER_PENDING" if pending_transfer else "CONFIRM_SWITCH",
                company_id=invite.company_id,
                company_name=company.company_name,
                invite_token=invite.invite_token,
                is_same_fleet=False,
                is_fleet_mismatch=True,
                current_company_id=driver.company_id,
                current_company_name=current_comp.company_name if current_comp else "Current Fleet",
                target_company_id=invite.company_id,
                target_company_name=company.company_name,
                driver_status=driver.status.value,
                verification_status=driver.verification_status.value if driver.verification_status else None,
                has_pending_transfer=bool(pending_transfer),
                message="Fleet switch detected. Confirmation required before transfer."
            )

    # Driver is not yet identified: prompt phone verification with fleet context
    return ResolveQrResponse(
        valid=True,
        action="VERIFY_PHONE",
        company_id=invite.company_id,
        company_name=company.company_name,
        invite_token=invite.invite_token,
        message="Fleet QR verified. Please verify mobile number to proceed."
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
    - If invite_token provided:
        * Same fleet: authenticate directly to account.
        * Different fleet: detect mismatch, do not overwrite assignment, return mismatch details.
        * New driver: register under target fleet.
    - If invite_token NOT provided (Direct Mobile Login):
        * Existing driver with fleet: login directly.
        * New driver without fleet: return 404 prompt to scan QR.
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

    # Validate invite token if provided
    invite = None
    target_company_id = None
    target_company = None
    if payload.invite_token:
        token = parse_qr_token(payload.invite_token)
        invite_result = await db.execute(
            select(FleetInvite).where(FleetInvite.invite_token == token)
        )
        invite = invite_result.scalar_one_or_none()
        if invite is None or not invite.is_valid:
            raise HTTPException(400, "Invalid or expired invite")
        target_company_id = invite.company_id
        target_company = invite.company
        if target_company is None or target_company.status != CompanyStatus.ACTIVE:
            raise HTTPException(400, "The fleet associated with this QR code is inactive.")

    # Find driver by normalized phone number
    driver = await find_driver_by_phone(payload.phone_number, db)

    is_new = driver is None

    if is_new and not target_company_id:
        raise HTTPException(
            status_code=404,
            detail="No driver profile found. Please scan a fleet QR code to join."
        )

    if is_new:
        # Create new user and driver under target_company_id
        disambiguated_phone = f"{payload.phone_number}_d{target_company_id}"

        user_result = await db.execute(
            select(User).where(
                User.mobile_number.in_([payload.phone_number, disambiguated_phone])
            )
        )
        existing_users = user_result.scalars().all()
        user_map = {u.mobile_number: u for u in existing_users}

        user = None
        if disambiguated_phone in user_map:
            user = user_map[disambiguated_phone]
        elif payload.phone_number in user_map:
            primary_user = user_map[payload.phone_number]
            if primary_user.company_id == target_company_id and primary_user.role == UserRole.DRIVER:
                user = primary_user
            else:
                user = User(
                    company_id=target_company_id,
                    full_name=payload.phone_number,
                    mobile_number=disambiguated_phone,
                    password_hash=hash_password(secrets.token_urlsafe(24)),
                    role=UserRole.DRIVER,
                    is_active=False,
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
        else:
            user = User(
                company_id=target_company_id,
                full_name=payload.phone_number,
                mobile_number=payload.phone_number,
                password_hash=hash_password(secrets.token_urlsafe(24)),
                role=UserRole.DRIVER,
                is_active=False,
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

        driver = Driver(
            name=payload.phone_number,
            phone_number=payload.phone_number,
            company_id=target_company_id,
            user_id=user.id,
            status=DriverStatus.INACTIVE,
            verification_status=VerificationStatus.PENDING_DOCUMENTS,
            origin_type="driver_app",
        )
        db.add(driver)
        try:
            async with db.begin_nested():
                await db.flush()
        except IntegrityError:
            driver_result = await db.execute(
                select(Driver).where(Driver.phone_number == payload.phone_number)
            )
            driver = driver_result.scalar_one()

        if invite is not None:
            invite.use_count += 1

        active_company_id = target_company_id
        is_mismatch = False
        target_comp_name = target_company.company_name if target_company else None
        current_comp_name = target_comp_name
        has_pending = False
    else:
        # Existing driver
        active_company_id = driver.company_id
        current_comp_name = driver.company.company_name if driver.company else None
        target_comp_name = target_company.company_name if target_company else None

        # Check for fleet mismatch if invite was provided
        if target_company_id is not None and driver.company_id != target_company_id:
            # IMPORTANT: Do NOT silently overwrite driver.company_id!
            # Preserve current fleet assignment and flag mismatch for user confirmation.
            is_mismatch = True
            
            # Check for existing pending transfer
            trans_res = await db.execute(
                select(DriverFleetTransfer).where(
                    DriverFleetTransfer.driver_id == driver.id,
                    DriverFleetTransfer.to_company_id == target_company_id,
                    DriverFleetTransfer.status == TransferStatus.PENDING_APPROVAL
                )
            )
            has_pending = trans_res.scalars().first() is not None
        else:
            is_mismatch = False
            has_pending = False
            if target_company_id is not None and invite is not None:
                invite.use_count += 1

    # Generate JWT session for driver under their currently authoritative company
    from models.auth_session import AuthSession
    jti = secrets.token_urlsafe(24)
    session = AuthSession(
        user_id=driver.user_id or 0,
        company_id=active_company_id or 0,
        session_jti=jti,
        remember_me=True,
        expires_at=datetime.now(tz=timezone.utc) + __import__('datetime').timedelta(days=30),
    )
    db.add(session)

    token = create_access_token(
        data={
            "sub": str(driver.user_id),
            "company_id": active_company_id,
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
        driver_status=driver.status.value,
        company_id=active_company_id,
        company_name=current_comp_name,
        is_fleet_mismatch=is_mismatch if not is_new else False,
        current_company_id=active_company_id,
        current_company_name=current_comp_name,
        target_company_id=target_company_id if is_mismatch else None,
        target_company_name=target_comp_name if is_mismatch else None,
        has_pending_transfer=has_pending,
    )


@router.post("/fleet-transfer", response_model=FleetTransferResponse)
async def create_fleet_transfer(
    payload: CreateFleetTransferRequest,
    driver: Driver = Depends(get_onboarding_driver),
    db: AsyncSession = Depends(get_db),
) -> FleetTransferResponse:
    """
    Start a new fleet transfer request for an existing driver to switch fleets.
    - Validates target company and invite token.
    - Ensures no concurrent conflicting pending transfers.
    - Reuses existing verified documents for the target company.
    - Marks transfer as PENDING_APPROVAL without modifying current active assignment.
    """
    if driver.company_id == payload.target_company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver is already assigned to this fleet."
        )

    # Validate invite token
    token = parse_qr_token(payload.invite_token)
    invite_result = await db.execute(
        select(FleetInvite).where(
            FleetInvite.invite_token == token,
            FleetInvite.company_id == payload.target_company_id
        )
    )
    invite = invite_result.scalar_one_or_none()
    if not invite or not invite.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired fleet invite QR code for target fleet."
        )

    # Validate target company
    target_comp = await db.get(Company, payload.target_company_id)
    if not target_comp or target_comp.status != CompanyStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target fleet company is inactive or not found."
        )

    # Check for existing pending transfers
    existing_transfers_res = await db.execute(
        select(DriverFleetTransfer).where(
            DriverFleetTransfer.driver_id == driver.id,
            DriverFleetTransfer.status == TransferStatus.PENDING_APPROVAL
        )
    )
    existing_transfers = existing_transfers_res.scalars().all()
    for existing in existing_transfers:
        if existing.to_company_id == payload.target_company_id:
            from_comp_name = driver.company.company_name if driver.company else "Unknown"
            return FleetTransferResponse(
                id=existing.id,
                driver_id=driver.id,
                from_company_id=driver.company_id or 0,
                from_company_name=from_comp_name,
                to_company_id=target_comp.id,
                to_company_name=target_comp.company_name,
                status=existing.status.value,
                created_at=existing.created_at,
                message="Fleet transfer request is already pending approval."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A transfer request to another fleet is already pending. Please cancel it before requesting a new transfer."
            )

    # Create transfer request
    transfer = DriverFleetTransfer(
        driver_id=driver.id,
        from_company_id=driver.company_id or 0,
        to_company_id=payload.target_company_id,
        invite_token=token,
        status=TransferStatus.PENDING_APPROVAL,
    )
    db.add(transfer)
    invite.use_count += 1

    # Reuse existing verified documents for target company
    from models.document import Document, DocumentVerificationStatus
    doc_res = await db.execute(
        select(Document).where(
            Document.target_id == str(driver.id),
            Document.target_type == "DRIVER"
        ).order_by(Document.created_at.desc())
    )
    docs = doc_res.scalars().all()
    copied_cats = set()
    for doc in docs:
        if doc.category and doc.category not in copied_cats:
            copied_cats.add(doc.category)
            if doc.verification_status == DocumentVerificationStatus.APPROVED:
                reused_doc = Document(
                    company_id=payload.target_company_id,
                    target_id=str(driver.id),
                    target_type="DRIVER",
                    category=doc.category,
                    original_filename=doc.original_filename,
                    storage_path=doc.storage_path,
                    mime_type=doc.mime_type,
                    status=doc.status,
                    verification_status=DocumentVerificationStatus.APPROVED,
                    metadata_extracted=doc.metadata_extracted,
                    uploaded_by=f"driver_transfer_{driver.id}",
                )
                db.add(reused_doc)

    # Notify target company admins
    notification = Notification(
        category=NotificationCategory.SYSTEM,
        title="Driver Fleet Transfer Request",
        description=f"Driver {driver.name} has requested to transfer into your fleet.",
        company_id=payload.target_company_id,
    )
    db.add(notification)

    await db.commit()
    await db.refresh(transfer)

    from_comp_name = driver.company.company_name if driver.company else "Unknown"
    return FleetTransferResponse(
        id=transfer.id,
        driver_id=driver.id,
        from_company_id=transfer.from_company_id,
        from_company_name=from_comp_name,
        to_company_id=target_comp.id,
        to_company_name=target_comp.company_name,
        status=transfer.status.value,
        created_at=transfer.created_at,
        message="Fleet transfer request submitted successfully. Awaiting fleet manager approval."
    )


@router.post("/fleet-transfer/{transfer_id}/cancel")
async def cancel_fleet_transfer(
    transfer_id: int,
    driver: Driver = Depends(get_onboarding_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an existing pending fleet transfer request.
    Preserves current fleet assignment completely.
    """
    result = await db.execute(
        select(DriverFleetTransfer).where(
            DriverFleetTransfer.id == transfer_id,
            DriverFleetTransfer.driver_id == driver.id,
        )
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=404, detail="Fleet transfer request not found.")

    if transfer.status != TransferStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel transfer in '{transfer.status.value}' state."
        )

    transfer.status = TransferStatus.CANCELLED
    await db.commit()

    return {"message": "Fleet transfer request cancelled successfully."}


# ==========================================================================
# Profile Endpoints
# ==========================================================================

from sqlalchemy.exc import IntegrityError

@router.post("/register", response_model=DriverProfileResponse)
async def register_driver_profile(
    payload: DriverProfileRequest,
    driver: Driver = Depends(get_onboarding_driver),
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

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The provided License Number or Aadhaar Number is already registered."
        )

    await db.refresh(driver)

    response = _driver_to_response(driver)
    response.assigned_vehicle = await _get_assigned_vehicle(driver.id, db)
    return response


@router.post("/upload-document")
async def upload_document(
    document_type: str = Form(..., description="license_front, license_back, aadhaar_front, aadhaar_back, selfie"),
    file: UploadFile = File(...),
    driver: Driver = Depends(get_onboarding_driver),
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
            document_type=document_type,
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
            driver.verification_status = VerificationStatus.PENDING_APPROVAL
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
    driver: Driver = Depends(get_onboarding_driver),
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
    driver: Driver = Depends(get_onboarding_driver),
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
    driver: Driver = Depends(get_onboarding_driver),
    db: AsyncSession = Depends(get_db),
):
    """Get driver profile with approval status and pending transfer."""
    response = _driver_to_response(driver)
    response.assigned_vehicle = await _get_assigned_vehicle(driver.id, db)
    response.pending_transfer = await _get_pending_transfer(driver.id, db)
    return response


@router.get("/me", response_model=DriverProfileResponse)
async def get_driver_me(
    driver: Driver = Depends(get_onboarding_driver),
    db: AsyncSession = Depends(get_db),
):
    """Authoritative driver profile endpoint including fleet and pending transfer."""
    response = _driver_to_response(driver)
    response.assigned_vehicle = await _get_assigned_vehicle(driver.id, db)
    response.pending_transfer = await _get_pending_transfer(driver.id, db)
    return response


@router.patch("/profile", response_model=DriverProfileResponse)
async def update_driver_profile(
    payload: DriverProfileRequest,
    driver: Driver = Depends(get_onboarding_driver),
    db: AsyncSession = Depends(get_db),
):
    """Update driver profile details."""
    if payload.name:
        driver.name = payload.name
    if payload.license_number:
        driver.license_number = payload.license_number

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The provided License Number is already registered."
        )
        
    await db.refresh(driver)
    response = _driver_to_response(driver)
    response.assigned_vehicle = await _get_assigned_vehicle(driver.id, db)
    return response


@router.put("/fcm-token")
async def update_fcm_token(
    payload: FcmTokenRequest,
    driver: Driver = Depends(get_onboarding_driver),
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


async def _get_pending_transfer(driver_id: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Helper to get any pending fleet transfer for this driver."""
    result = await db.execute(
        select(DriverFleetTransfer)
        .where(
            DriverFleetTransfer.driver_id == driver_id,
            DriverFleetTransfer.status == TransferStatus.PENDING_APPROVAL
        )
        .order_by(DriverFleetTransfer.created_at.desc())
        .limit(1)
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        return None
    return {
        "id": transfer.id,
        "from_company_id": transfer.from_company_id,
        "from_company_name": transfer.from_company.company_name if transfer.from_company else "Unknown",
        "to_company_id": transfer.to_company_id,
        "to_company_name": transfer.to_company.company_name if transfer.to_company else "Unknown",
        "status": transfer.status.value,
        "created_at": transfer.created_at.isoformat() if transfer.created_at else None,
    }

