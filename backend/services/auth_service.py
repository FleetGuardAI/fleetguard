"""
FleetGuard — Authentication Service

All authentication business logic lives here. Routers are kept intentionally
thin and delegate entirely to this module.

Responsibilities:
  - Company registration (atomic: company + admin user + JWT)
  - Dual-identifier login (email OR mobile number)
  - JWT creation and decoding
  - FastAPI dependency: get_current_user()
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.company import Company, CompanyStatus
from models.user import User, UserRole
from schemas.auth import (
    CompanyOut,
    CompanyRegistrationRequest,
    RegisterCompanyResponse,
    TokenResponse,
    UserOut,
)

logger = logging.getLogger("fleetguard.auth")

# ---------------------------------------------------------------------------
# Security primitives
# ---------------------------------------------------------------------------

# bcrypt context — auto-selects best available rounds
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 bearer scheme — tokenUrl is informational for Swagger UI
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------------------------------------------------------------------------
# Internal helpers — not exported; used only within this module
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*. Never store raw passwords."""
    return _pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*. Constant-time comparison."""
    return _pwd_context.verify(plain, hashed)


def _build_token_payload(user: User) -> dict:
    """
    Assemble the JWT claims dict for *user*.

    Claims kept minimal — only what is needed to authorise a request
    without a DB round-trip on every call.
    """
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return {
        "sub": str(user.id),          # subject: user PK (string per JWT spec)
        "company_id": user.company_id,
        "role": user.role.value,
        "exp": expire,
    }


def _create_access_token(user: User) -> str:
    """
    Encode a signed JWT for *user*.

    Algorithm and secret are read from settings so they can be overridden
    per environment without code changes.
    """
    payload = _build_token_payload(user)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


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
    Raise HTTP 409 if *mobile* already exists in the users table.

    *exclude_user_id* is reserved for future "update profile" use-cases
    where the mobile owner is the user being updated.
    """
    q = select(User).where(User.mobile_number == mobile)
    if exclude_user_id is not None:
        q = q.where(User.id != exclude_user_id)
    result = await db.execute(q)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This mobile number is already registered.",
        )


async def _assert_email_not_taken(
    email: str, db: AsyncSession, *, exclude_user_id: Optional[int] = None
) -> None:
    """
    Raise HTTP 409 if *email* already exists in the users table.
    Only called when an email is actually provided.
    """
    q = select(User).where(User.email == email)
    if exclude_user_id is not None:
        q = q.where(User.id != exclude_user_id)
    result = await db.execute(q)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already registered.",
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
            password_hash=_hash_password(payload.password),
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
        )
        db.add(admin_user)
        # 5. Flush → get user.id so we can encode it in the token
        await db.flush()

        # 6. Issue token while still in the transaction
        access_token = _create_access_token(admin_user)

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
        token=TokenResponse(access_token=access_token),
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
        _pwd_context.dummy_verify()
        raise _INVALID_CREDENTIALS

    if not _verify_password(password, user.password_hash):
        raise _INVALID_CREDENTIALS

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact your administrator.",
        )

    logger.info("Successful login: user_id=%d, role=%s", user.id, user.role.value)
    return user


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
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise _CREDENTIALS_EXCEPTION
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise _CREDENTIALS_EXCEPTION

    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()

    if user is None:
        raise _CREDENTIALS_EXCEPTION

    # Enforce is_active on every authenticated request — catches mid-session deactivation
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated.",
        )

    return user


def create_token_for_user(user: User) -> TokenResponse:
    """
    Generate and return a TokenResponse for *user*.

    Exposed as a standalone function so the login router can call it
    without duplicating token-creation logic.
    """
    return TokenResponse(access_token=_create_access_token(user))
