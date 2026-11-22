import os
import pytest
from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from services.admin_auth_service import (
    get_admin_jwt_secret,
    create_access_token,
    get_current_admin,
    ALGORITHM,
    _TEST_ADMIN_SECRET,
)
from models.admin_domain import AdminUser
from utils.security import create_access_token as create_user_jwt, hash_password


def test_admin_jwt_secret_enforcement():
    """FG-SEC-003: Admin JWT secret enforces minimum 32 chars and rejects weak keys."""
    # Test weak secret (< 32 chars)
    original_secret = getattr(settings, "ADMIN_JWT_SECRET", None)
    try:
        settings.ADMIN_JWT_SECRET = "too-short-key"
        with pytest.raises(RuntimeError, match="at least 32 characters"):
            get_admin_jwt_secret()

        # Test valid secret >= 32 chars
        valid_key = "a" * 32
        settings.ADMIN_JWT_SECRET = valid_key
        assert get_admin_jwt_secret() == valid_key
    finally:
        settings.ADMIN_JWT_SECRET = original_secret


@pytest.mark.asyncio
async def test_startup_fails_in_production_with_weak_admin_secret():
    """FG-SEC-003: Application lifespan startup fails if ADMIN_JWT_SECRET is weak."""
    from main import lifespan
    from fastapi import FastAPI
    dummy_app = FastAPI()
    original_secret = getattr(settings, "ADMIN_JWT_SECRET", None)
    try:
        settings.ADMIN_JWT_SECRET = "short_key_123"
        with pytest.raises(RuntimeError, match="at least 32 characters"):
            async with lifespan(dummy_app):
                pass
    finally:
        settings.ADMIN_JWT_SECRET = original_secret


@pytest.mark.asyncio
async def test_user_jwt_cannot_access_admin(db_session: AsyncSession):
    """
    FG-SEC-003: A regular user JWT signed with SECRET_KEY is rejected
    by get_current_admin due to token_type and signing secret isolation.
    """
    # Create regular user token (signed with SECRET_KEY, token_type='access')
    user_payload = {
        "sub": "1",
        "company_id": 1,
        "role": "COMPANY_ADMIN",
        "type": "access",
        "jti": "some-jti-123",
    }
    regular_user_token = create_user_jwt(user_payload)

    # Attempt to use regular user token as admin token
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(token=regular_user_token, db=db_session)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_admin_token_type_validation(db_session: AsyncSession):
    """FG-SEC-003: Token signed with admin key but missing token_type=admin_access is rejected."""
    # Create token signed with admin key, but without token_type='admin_access'
    fake_payload = {
        "admin_id": "1",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "token_type": "access",  # wrong type
    }
    fake_token = jwt.encode(fake_payload, get_admin_jwt_secret(), algorithm=ALGORITHM)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(token=fake_token, db=db_session)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_valid_admin_token_accepted(db_session: AsyncSession):
    """FG-SEC-003: A valid admin token resolves the active admin user."""
    from models.admin_domain import AdminRole, AdminRoleType
    from sqlalchemy import select

    # Find or create an AdminRole
    res = await db_session.execute(select(AdminRole).where(AdminRole.name == AdminRoleType.ADMIN))
    role = res.scalar_one_or_none()
    if not role:
        role = AdminRole(name=AdminRoleType.ADMIN, description="Administrator")
        db_session.add(role)
        await db_session.flush()

    # Create test admin user in DB
    admin = AdminUser(
        email="security_test_admin@fleetguard.com",
        password_hash=hash_password("adminpass123"),
        full_name="Security Admin",
        role_id=role.id,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    token = create_access_token({"admin_id": str(admin.id)})
    resolved_admin = await get_current_admin(token=token, db=db_session)
    assert resolved_admin.id == admin.id
    assert resolved_admin.email == "security_test_admin@fleetguard.com"
