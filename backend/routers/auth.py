"""
FleetGuard — Authentication Router

Handles public tenant registration, dual-identifier login (email or mobile),
and retrieval of current user profile context.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from schemas import (
    CompanyOut,
    CompanyRegistrationRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GenericMessageResponse,
    LoginRequest,
    MeResponse,
    RegisterCompanyResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
    CompanyUpdateRequest,
    OwnerQRLoginRequest,
    OwnerQRPairingResponse,
)
from services import (
    authenticate_user,
    create_forgot_password_request,
    create_token_for_user,
    get_current_user,
    register_company,
    reset_password_with_token,
    logout_user,
    _oauth2_scheme,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterCompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new company and its admin user",
)
async def register(
    payload: CompanyRegistrationRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterCompanyResponse:
    """
    Register a new transport company.

    Atomically creates a new Company tenant and the first primary Admin user,
    hashes the password, generates a JWT access token, and returns the context.
    """
    return await register_company(payload=payload, db=db)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user and return a JWT access token",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Log in using email OR mobile number.

    The router resolves the provided identifier and delegates verification to the
    auth service. Returns a JWT access token.
    """
    # Guaranteed by schemas/auth.py validation that at least one is present
    login_identifier = payload.email if payload.email is not None else payload.mobile_number
    
    user = await authenticate_user(
        login_identifier=login_identifier,
        password=payload.password,
        db=db,
    )
    return await create_token_for_user(
        user=user,
        db=db,
        remember_me=payload.remember_me,
    )



@router.post(
    "/forgot-password/request",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Start forgot-password flow",
)
async def forgot_password_request(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
    """Generate one-time password reset token for an account identifier."""
    return await create_forgot_password_request(payload=payload, db=db)


@router.post(
    "/forgot-password/reset",
    response_model=GenericMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password using one-time token",
)
async def forgot_password_reset(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> GenericMessageResponse:
    """Finalize password reset and revoke active sessions for the account."""
    return await reset_password_with_token(payload=payload, db=db)


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get details of the currently logged-in user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> MeResponse:
    """
    Retrieve profile details, role, and company details for the active session.

    Requires a valid Bearer JWT token in the Authorization header.
    """
    return MeResponse(
        user=UserOut.model_validate(current_user),
        company=CompanyOut.model_validate(current_user.company),
        role=current_user.role,
    )


@router.patch(
    "/company",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update details of the company for the active session",
)
async def update_company(
    payload: CompanyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """
    Update company registration details.
    Restricted to COMPANY_ADMIN.
    Updates both the company record and the admin user profile to maintain integrity.
    """
    company = current_user.company

    update_data = payload.model_dump(exclude_unset=True)

    # Update company record
    if "company_name" in update_data:
        company.company_name = update_data["company_name"]
    if "owner_name" in update_data:
        company.owner_name = update_data["owner_name"]
        current_user.full_name = update_data["owner_name"]
    if "mobile_number" in update_data:
        company.mobile_number = update_data["mobile_number"]
        current_user.mobile_number = update_data["mobile_number"]
    if "email" in update_data:
        company.email = update_data["email"] or None
        current_user.email = update_data["email"] or None

    await db.flush()
    await db.refresh(company)
    await db.refresh(current_user)

    return MeResponse(
        user=UserOut.model_validate(current_user),
        company=CompanyOut.model_validate(company),
        role=current_user.role,
    )


@router.post(
    "/logout",
    response_model=GenericMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out the current session",
)
async def logout(
    token: str = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> GenericMessageResponse:
    """
    Revoke the current user's session.
    """
    await logout_user(token, db)
    return GenericMessageResponse(message="Successfully logged out.")


@router.post(
    "/owner-qr/generate",
    response_model=OwnerQRPairingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a short-lived QR token for Owner App login",
)
async def generate_owner_qr(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OwnerQRPairingResponse:
    """
    Generate a pairing token for the Owner App.
    Only COMPANY_ADMIN can generate this.
    """
    from models.user import UserRole
    if current_user.role not in (UserRole.COMPANY_ADMIN, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Company Admin can generate Owner App QR codes."
        )
    
    from services.auth_service import generate_owner_qr_token
    return await generate_owner_qr_token(current_user, db)


@router.post(
    "/owner-qr/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify QR token and return access token for Owner App",
)
async def verify_owner_qr(
    payload: OwnerQRLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Verify the scanned QR token. If valid, create AuthSession and return JWT.
    """
    from services.auth_service import verify_owner_qr_token
    return await verify_owner_qr_token(payload.pairing_token, db)




