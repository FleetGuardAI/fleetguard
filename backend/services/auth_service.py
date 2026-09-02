"""
FleetGuard — Authentication Service

All authentication business logic lives here. Routers are kept intentionally
thin and delegate entirely to this module.

Responsibilities:
  - Company registration (atomic: company + admin user + JWT)
  - Dual-identifier login (email OR mobile number)
  - Remember-me session persistence with company/user mapping
  - Forgot-password and reset-password token workflows
  - JWT creation and decoding
  - FastAPI dependency: get_current_user()
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.auth_session import AuthSession
from models.company import Company, CompanyStatus
from models.password_reset_token import PasswordResetToken
from models.user import User, UserRole
from schemas.auth import (
    CompanyOut,
    CompanyRegistrationRequest,
        ForgotPasswordRequest,
        ForgotPasswordResponse,
        GenericMessageResponse,
    RegisterCompanyResponse,
        ResetPasswordRequest,
    TokenResponse,
    UserOut,
)

logger = logging.getLogger("fleetguard.auth")

from utils.security import (
    create_access_token,
    decode_access_token,
    dummy_verify,
    hash_password,
    verify_password,
)

# OAuth2 bearer scheme — tokenUrl is informational for Swagger UI
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------------------------------------------------------------------------
# Internal helpers — not exported; used only within this module
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _build_token_payload(user: User, jti: str, remember_me: bool) -> dict:
    """
    Assemble the JWT claims dict for *user*.

    Claims kept minimal — only what is needed to authorise a request
    without a DB round-trip on every call.
    """
    return {
        "sub": str(user.id),          # subject: user PK (string per JWT spec)
        "company_id": user.company_id,
        "role": user.role.value,
        "jti": jti,
        "remember_me": remember_me,
    }


def _session_expiry(remember_me: bool) -> datetime:
    if remember_me:
        return _utcnow() + timedelta(days=settings.REMEMBER_ME_EXPIRE_DAYS)
    return _utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def _create_access_token(user: User, jti: str, remember_me: bool) -> str:
    """
    Encode a signed JWT for *user*.
    """
    payload = _build_token_payload(user, jti=jti, remember_me=remember_me)
    payload["type"] = "access"
    return create_access_token(
        payload,
        expires_delta=(_session_expiry(remember_me) - _utcnow()),
    )

def _create_refresh_token(user: User, jti: str, remember_me: bool) -> str:
    payload = _build_token_payload(user, jti=jti, remember_me=remember_me)
    payload["type"] = "refresh"
    # Refresh tokens last longer (e.g., 30 days)
    expires_delta = timedelta(days=30)
    return create_access_token(payload, expires_delta=expires_delta)


def _user_to_out(user: User) -> UserOut:
    """
    Safely convert a User ORM instance → UserOut schema.

    Handles the `last_login` field which does not yet exist on the ORM model;
    it defaults to None and will be populated once that column is added.
    """
    return UserOut(
        id=user.id,
        company_id=user.company_id,
        full_name=user.full_name,
        mobile_number=user.mobile_number,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login=getattr(user, "last_login", None),
    )


async def _assert_mobile_not_taken(
    mobile: str, db: AsyncSession, *, exclude_user_id: Optional[int] = None
) -> None:
    """
    Raise HTTP 409 if *mobile* already exists in users or companies table.
    """
    q1 = select(User).where(User.mobile_number == mobile)
    if exclude_user_id is not None:
        q1 = q1.where(User.id != exclude_user_id)
    res1 = await db.execute(q1)
    if res1.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already registered with this mobile number. Please log in.",
        )

    q2 = select(Company).where(Company.mobile_number == mobile)
    res2 = await db.execute(q2)
    if res2.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already registered with this mobile number. Please log in.",
        )


async def _assert_email_not_taken(
    email: str, db: AsyncSession, *, exclude_user_id: Optional[int] = None
) -> None:
    """
    Raise HTTP 409 if *email* already exists in users or companies table.
    """
    if not email:
        return
    q1 = select(User).where(User.email == email)
    if exclude_user_id is not None:
        q1 = q1.where(User.id != exclude_user_id)
    res1 = await db.execute(q1)
    if res1.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already registered with this email address. Please log in.",
        )

    q2 = select(Company).where(Company.email == email)
    res2 = await db.execute(q2)
    if res2.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already registered with this email address. Please log in.",
        )




# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

async def register_company(
    payload: CompanyRegistrationRequest,
    db: AsyncSession,
) -> RegisterCompanyResponse:
    """
    Register a new company and create its first COMPANY_ADMIN user.

    The entire operation is atomic: if anything fails after the company row
    is inserted (e.g., a race-condition duplicate on the user insert), the
    session is rolled back by the ``get_db`` dependency and no partial data
    is persisted.

    Steps
    -----
    1. Pre-flight uniqueness checks (fast, readable 409 errors).
    2. Create Company row.
    3. Flush to obtain company.id (still within the transaction).
    4. Create User row referencing company.id.
    5. Flush to obtain user.id.
    6. Issue JWT (pure in-memory — no DB write).
    7. Commit.  The ``get_db`` dependency calls commit on successful yield.
    8. Refresh both ORM objects so all server-defaults (timestamps) load.
    9. Build and return the response schema.
    """
    # 1. Uniqueness pre-flight
    await _assert_mobile_not_taken(payload.mobile_number, db)
    if payload.email:
        await _assert_email_not_taken(payload.email, db)

    try:
        # 2. Create company
        company = Company(
            company_name=payload.company_name,
            owner_name=payload.owner_name,
            mobile_number=payload.mobile_number,
            email=payload.email or None,
            status=CompanyStatus.ACTIVE,
        )
        db.add(company)
        # 3. Flush → get company.id without committing
        await db.flush()

        # 4. Create the primary admin user
        admin_user = User(
            company_id=company.id,
            full_name=payload.owner_name,
            mobile_number=payload.mobile_number,
            email=payload.email or None,
            password_hash=hash_password(payload.password),
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
        )
        db.add(admin_user)
        # 5. Flush → get user.id so we can encode it in the token
        await db.flush()

        # 6. Issue token while still in the transaction
        token = await create_token_for_user(admin_user, db=db, remember_me=True)

        # 7. Commit is handled by get_db on successful exit — nothing to do here.

        # 8. Refresh to load server-default columns (timestamps, status enum)
        await db.refresh(company)
        await db.refresh(admin_user)

    except IntegrityError as exc:
        # Surface-safe message — do NOT leak raw DB constraint text to clients
        logger.warning("register_company IntegrityError: %s", exc.orig)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration failed: duplicate mobile number or email address.",
        ) from exc

    logger.info(
        "Company registered: id=%d name='%s', admin user id=%d",
        company.id,
        company.company_name,
        admin_user.id,
    )

    # 9. Build response — never touch password_hash
    return RegisterCompanyResponse(
        company=CompanyOut.model_validate(company),
        user=_user_to_out(admin_user),
        token=token,
    )


async def authenticate_user(
    login_identifier: str,
    password: str,
    db: AsyncSession,
) -> User:
    """
    Verify credentials and return the authenticated User ORM object.

    The caller (router) is responsible for building the token response.

    Detection logic
    ---------------
    - If *login_identifier* contains "@"  → treat as email.
    - Otherwise                           → treat as mobile number.

    Errors are intentionally vague to prevent user-enumeration attacks.
    A timing-safe dummy verification is run even when the user is not found
    so that response times remain consistent.
    """
    _INVALID_CREDENTIALS = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # --- Resolve lookup strategy ---
    if "@" in login_identifier:
        query = select(User).where(User.email == login_identifier)
        logger.debug("Login attempt via email: %s", login_identifier)
    else:
        query = select(User).where(User.mobile_number == login_identifier)
        logger.debug("Login attempt via mobile: %s", login_identifier)

    result = await db.execute(query)
    user: Optional[User] = result.scalar_one_or_none()

    if user is None:
        # Run a dummy verify to keep response time constant (timing-attack mitigation)
        dummy_verify()
        raise _INVALID_CREDENTIALS

    if not verify_password(password, user.password_hash):
        raise _INVALID_CREDENTIALS

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact your administrator.",
        )

    logger.info("Successful login: user_id=%d, role=%s", user.id, user.role.value)
    return user


async def create_forgot_password_request(
    payload: ForgotPasswordRequest,
    db: AsyncSession,
) -> ForgotPasswordResponse:
    """Create one-time password reset token while preserving account privacy."""
    identifier = payload.identifier.strip()
    now = _utcnow()
    generic_message = (
        "If an account exists for that identifier, password reset instructions were generated."
    )

    if "@" in identifier:
        result = await db.execute(select(User).where(User.email == identifier))
    else:
        result = await db.execute(select(User).where(User.mobile_number == identifier))

    user = result.scalar_one_or_none()
    if user is None:
        dummy_verify()
        return ForgotPasswordResponse(message=generic_message)

    # Invalidate prior active reset tokens for this user
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .values(used_at=now)
    )

    raw_token = secrets.token_urlsafe(36)
    expires_at = now + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
    reset_entry = PasswordResetToken(
        user_id=user.id,
        company_id=user.company_id,
        token_hash=_hash_token(raw_token),
        requested_identifier=identifier,
        expires_at=expires_at,
    )
    db.add(reset_entry)

    if settings.DEBUG and settings.PASSWORD_RESET_DEBUG_RETURN_TOKEN:
        return ForgotPasswordResponse(
            message=generic_message,
            reset_token=raw_token,
            expires_at=expires_at,
        )

    logger.info(
        "Password reset requested: user_id=%d company_id=%d",
        user.id,
        user.company_id,
    )
    return ForgotPasswordResponse(message=generic_message)


async def reset_password_with_token(
    payload: ResetPasswordRequest,
    db: AsyncSession,
) -> GenericMessageResponse:
    """Reset password using valid one-time token and revoke all active sessions."""
    now = _utcnow()
    token_hash = _hash_token(payload.reset_token)

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    )
    reset_entry = result.scalar_one_or_none()
    if reset_entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid or expired.",
        )

    user_result = await db.execute(
        select(User).where(
            User.id == reset_entry.user_id,
            User.company_id == reset_entry.company_id,
        )
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not resolve account for this reset token.",
        )

    user.password_hash = hash_password(payload.new_password)
    reset_entry.used_at = now

    await db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )

    logger.info("Password reset completed: user_id=%d company_id=%d", user.id, user.company_id)
    return GenericMessageResponse(message="Password has been reset successfully.")


async def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that decodes the Bearer JWT and returns the live User.

    Usage in a router
    -----------------
    ::

        @router.get("/me")
        async def me(current_user: User = Depends(get_current_user)):
            ...

    Raises HTTP 401 on any token issue (expired, tampered, unknown user).
    """
    _CREDENTIALS_EXCEPTION = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        token_jti: Optional[str] = payload.get("jti")
        token_company_id: Optional[int] = payload.get("company_id")
        if user_id_str is None:
            raise _CREDENTIALS_EXCEPTION
        if token_jti is None:
            raise _CREDENTIALS_EXCEPTION
        if payload.get("type") == "refresh":
            raise _CREDENTIALS_EXCEPTION
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise _CREDENTIALS_EXCEPTION

    now = _utcnow()
    session_result = await db.execute(
        select(AuthSession).where(
            AuthSession.session_jti == token_jti,
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
    )
    auth_session = session_result.scalar_one_or_none()
    if auth_session is None:
        raise _CREDENTIALS_EXCEPTION

    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()

    if user is None:
        raise _CREDENTIALS_EXCEPTION
    if token_company_id is not None and user.company_id != int(token_company_id):
        raise _CREDENTIALS_EXCEPTION

    # Enforce is_active on every authenticated request — catches mid-session deactivation
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated.",
        )

    auth_session.last_seen_at = now
    return user


async def create_token_for_user(
    user: User,
    db: AsyncSession,
    *,
    remember_me: bool = False,
) -> TokenResponse:
    """
    Generate and return a TokenResponse for *user*.

    Exposed as a standalone function so the login router can call it
    without duplicating token-creation logic.
    """
    jti = secrets.token_urlsafe(24)
    session = AuthSession(
        user_id=user.id,
        company_id=user.company_id,
        session_jti=jti,
        remember_me=remember_me,
        expires_at=_session_expiry(remember_me),
    )
    db.add(session)

    return TokenResponse(
        access_token=_create_access_token(user, jti=jti, remember_me=remember_me),
        refresh_token=_create_refresh_token(user, jti=jti, remember_me=remember_me),
        token_type="bearer",
    )


async def logout_user(token: str, db: AsyncSession) -> None:
    """Revoke the current session by JTI."""
    try:
        payload = decode_access_token(token)
        token_jti = payload.get("jti")
        if token_jti:
            await db.execute(
                update(AuthSession)
                .where(AuthSession.session_jti == token_jti)
                .values(revoked_at=_utcnow())
            )
    except JWTError:
        pass  # Just ignore if token is invalid

async def refresh_access_token(refresh_token: str, db: AsyncSession) -> TokenResponse:
    _CREDENTIALS_EXCEPTION = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(refresh_token)
        if payload.get("type") != "refresh":
            raise _CREDENTIALS_EXCEPTION
        user_id_str: Optional[str] = payload.get("sub")
        token_jti: Optional[str] = payload.get("jti")
        if user_id_str is None or token_jti is None:
            raise _CREDENTIALS_EXCEPTION
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise _CREDENTIALS_EXCEPTION

    now = _utcnow()
    session_result = await db.execute(
        select(AuthSession).where(
            AuthSession.session_jti == token_jti,
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None)
        )
    )
    auth_session = session_result.scalar_one_or_none()
    if auth_session is None:
        raise _CREDENTIALS_EXCEPTION
        
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXCEPTION
        
    # Optional: we can roll the refresh token or keep the same session.
    # To keep the session, we just issue a new access token (and same refresh token)
    return TokenResponse(
        access_token=_create_access_token(user, jti=token_jti, remember_me=auth_session.remember_me),
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def generate_owner_qr_token(user: User, db: AsyncSession):
    from models.owner_pairing_token import OwnerPairingToken
    from schemas.auth import OwnerQRPairingResponse
    from datetime import datetime, timezone
    
    # Invalidate existing unused tokens for this company
    now_utc = datetime.now(tz=timezone.utc)
    await db.execute(
        update(OwnerPairingToken)
        .where(
            OwnerPairingToken.company_id == user.company_id,
            OwnerPairingToken.is_used == False,
            OwnerPairingToken.expires_at > now_utc
        )
        .values(is_used=True)
    )

    raw_token = secrets.token_urlsafe(32)
    token_entry = OwnerPairingToken(
        company_id=user.company_id,
        user_id=user.id,
        pairing_token=raw_token,
    )
    db.add(token_entry)
    await db.commit()
    await db.refresh(token_entry)
    
    # Calculate expires_in_seconds
    now = datetime.utcnow()
    expires_at = token_entry.expires_at.replace(tzinfo=None)
    expires_in = int((expires_at - now).total_seconds())
    
    return OwnerQRPairingResponse(
        pairing_token=token_entry.pairing_token,
        expires_in_seconds=expires_in,
    )


async def verify_owner_qr_token(token: str, db: AsyncSession) -> TokenResponse:
    from models.owner_pairing_token import OwnerPairingToken
    import logging
    
    logger = logging.getLogger("fleetguard.auth")
    logger.info(f"[QR Verify] Received token format: {type(token)}, length: {len(token)}")
    from datetime import datetime, timezone
    
    token = token.strip()
    now_utc = datetime.now(tz=timezone.utc)
    
    # Atomically mark the token as used if it is valid
    result = await db.execute(
        update(OwnerPairingToken)
        .where(
            OwnerPairingToken.pairing_token == token,
            OwnerPairingToken.is_used == False,
            OwnerPairingToken.expires_at > now_utc
        )
        .values(is_used=True)
        .returning(OwnerPairingToken.user_id)
    )
    user_id = result.scalar_one_or_none()
    
    if user_id is None:
        logger.warning(f"[QR Verify] Token lookup failed. Not found in database or already used.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired QR token."
        )
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        logger.warning(f"[QR Verify] User validation failed. User is None: {user is None}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled or deleted."
        )
        
    logger.info(f"[QR Verify] Success for user {user.id} (Company: {user.company_id})")
    return await create_token_for_user(user, db=db, remember_me=True)
async def request_otp(identifier: str, db: AsyncSession):
    from schemas.auth import OTPRequestResponse
    from services.otp_service import otp_provider
    generic_message = "If an account exists for that identifier, a verification code has been sent."
    identifier = identifier.strip()
    
    if "@" in identifier:
        result = await db.execute(select(User).where(User.email == identifier))
        user = result.scalar_one_or_none()
    else:
        result = await db.execute(select(User).where(User.mobile_number == identifier))
        user = result.scalar_one_or_none()
        
        # Check normalized identifier (e.g. +91 prefix)
        if user is None:
            normalized_identifier = identifier
            if len(identifier) == 10 and identifier.isdigit():
                normalized_identifier = f"+91{identifier}"
            elif identifier.startswith("91") and len(identifier) == 12:
                normalized_identifier = f"+{identifier}"
            
            if normalized_identifier != identifier:
                result = await db.execute(select(User).where(User.mobile_number == normalized_identifier))
                user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        dummy_verify()
        return OTPRequestResponse(message=generic_message, req_id=None)
        
    result = await otp_provider.request_otp(identifier)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {result.message}"
        )
    return OTPRequestResponse(message=generic_message, req_id=result.provider_reference)

async def resend_otp(req_id: str, channel: str, db: AsyncSession):
    from schemas.auth import OTPRequestResponse
    from services.otp_service import otp_provider
    
    if req_id is None:
        # Prevents enumeration if they try to resend to a null req_id
        return OTPRequestResponse(message="OTP resent successfully.", req_id=None)
        
    result = await otp_provider.retry_otp(req_id, channel)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend OTP: {result.message}"
        )
    return OTPRequestResponse(message="OTP resent successfully.", req_id=result.provider_reference)

async def verify_otp(identifier: str, req_id: Optional[str], code: Optional[str], db: AsyncSession, msg91_token: Optional[str] = None) -> TokenResponse:
    from services.otp_service import otp_provider
    
    identifier = identifier.strip()
    if "@" in identifier:
        result = await db.execute(select(User).where(User.email == identifier))
        user = result.scalar_one_or_none()
    else:
        # Check raw identifier
        result = await db.execute(select(User).where(User.mobile_number == identifier))
        user = result.scalar_one_or_none()
        
        # Check normalized identifier (e.g. +91 prefix)
        if user is None:
            normalized_identifier = identifier
            if len(identifier) == 10 and identifier.isdigit():
                normalized_identifier = f"+91{identifier}"
            elif identifier.startswith("91") and len(identifier) == 12:
                normalized_identifier = f"+{identifier}"
            
            if normalized_identifier != identifier:
                result = await db.execute(select(User).where(User.mobile_number == normalized_identifier))
                user = result.scalar_one_or_none()
    
    if user is None:
        dummy_verify()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact your administrator.",
        )
        
    if msg91_token:
        otp_result = await otp_provider.verify_access_token(msg91_token)
    else:
        if not req_id or not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing req_id or code for OTP verification."
            )
        otp_result = await otp_provider.verify_otp(req_id, code)
        
    if not otp_result.success:
        if "MSG91 not fully configured" in otp_result.message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify OTP: {otp_result.message}"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    logger.info("Successful OTP login: user_id=%d, role=%s", user.id, user.role.value)
    return await create_token_for_user(user, db=db, remember_me=True)
