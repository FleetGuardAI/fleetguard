"""
FleetGuard — Phase B, Batch 8 Security Verification Suite
Tests:
1. FG-SEC-053: Access Token Lifetime Hardening (60m) & Decoupling from remember_me
2. FG-SEC-054: Expired Session Revocation Bypass Prevention in Refresh Token Flow
3. FG-SEC-055: Admin JWT JTI Tracking & Invalidation/Revocation
4. FG-SEC-051: Check-Then-Act Concurrency Lock on Maintenance Costs
5. FG-SEC-056: Double URL Prefix Cleanup (/api/v1/sos without /api/v1/v1)
6. FG-SEC-057: Deprecated In-Memory Fuel Shadow Mount Removal
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from jose import jwt
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from main import app
from config import settings
from database import get_db
from models.user import User, UserRole
from models.company import Company
from models.vehicle_domain import Vehicle
from models.auth_session import AuthSession
from models.admin_domain import AdminUser, AdminRole, AdminRoleType
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus, MaintenanceCategory
from services.auth_service import (
    _create_access_token,
    _create_refresh_token,
    refresh_access_token,
    decode_access_token,
    _utcnow,
)
from services.admin_auth_service import (
    create_access_token as create_admin_token,
    get_current_admin,
    get_admin_jwt_secret,
    revoke_admin_token,
    revoke_all_admin_tokens_for_user,
    is_admin_token_revoked,
    clear_admin_revocations_for_testing,
    ACCESS_TOKEN_EXPIRE_MINUTES as ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM as ADMIN_ALGORITHM,
)
from routers.maintenance_domain import _get_locked_maintenance_record
from utils.security import hash_password


# ==============================================================================
# 1. FG-SEC-053: Access Token Lifetime Hardening (60m Max Expiration)
# ==============================================================================

def test_access_token_expiration_settings_bounded_to_60_minutes():
    """Verify global config and admin auth constants enforce 60-minute token lifetimes."""
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60, (
        f"Expected ACCESS_TOKEN_EXPIRE_MINUTES == 60, got {settings.ACCESS_TOKEN_EXPIRE_MINUTES}"
    )
    assert ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES == 60, (
        f"Expected admin ACCESS_TOKEN_EXPIRE_MINUTES == 60, got {ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES}"
    )


def test_user_access_token_decoupled_from_remember_me():
    """
    FG-SEC-053: Access token lifetime must strictly expire in 60 minutes
    even when remember_me=True. Access tokens are stateless and must never live for 30 days.
    """
    user = User(
        id=12345,
        company_id=1,
        full_name="Driver User",
        mobile_number="9876543210",
        role=UserRole.DRIVER,
        is_active=True,
    )
    jti = "test-jti-token-123"

    # Token with remember_me=False
    token_standard = _create_access_token(user, jti=jti, remember_me=False)
    payload_standard = decode_access_token(token_standard)
    exp_standard = payload_standard["exp"]
    iat_standard = payload_standard.get("iat", int(datetime.now(timezone.utc).timestamp()))
    duration_standard = exp_standard - iat_standard

    # Should be approximately 3600 seconds (60 minutes)
    assert 3500 <= duration_standard <= 3660, (
        f"Standard access token lifetime was {duration_standard}s; expected ~3600s"
    )

    # Token with remember_me=True
    token_remember = _create_access_token(user, jti=jti, remember_me=True)
    payload_remember = decode_access_token(token_remember)
    exp_remember = payload_remember["exp"]
    iat_remember = payload_remember.get("iat", int(datetime.now(timezone.utc).timestamp()))
    duration_remember = exp_remember - iat_remember

    # MUST STILL BE ~3600s, NEVER 30 days (2,592,000s)
    assert 3500 <= duration_remember <= 3660, (
        f"Remember-me access token lifetime was {duration_remember}s; must be bounded to ~3600s"
    )


def test_admin_access_token_lifetime_bounded():
    """FG-SEC-053: Admin JWT access tokens expire in 60 minutes, not 12 hours."""
    token = create_admin_token(data={"admin_id": "42", "role": "SUPER_ADMIN"})
    payload = jwt.decode(token, get_admin_jwt_secret(), algorithms=[ADMIN_ALGORITHM])
    exp = payload["exp"]
    iat = payload.get("iat", int(datetime.now(timezone.utc).timestamp()))
    duration = exp - iat

    assert 3500 <= duration <= 3660, (
        f"Admin access token lifetime was {duration}s; expected ~3600s (60 min)"
    )


# ==============================================================================
# 2. FG-SEC-054: Expired Session Revocation Bypass in Refresh Flow
# ==============================================================================

@pytest.mark.asyncio
async def test_refresh_token_expired_session_rejected(db_session):
    """
    FG-SEC-054: An expired AuthSession (expires_at <= now) must NOT be refreshed.
    Prevents infinite access token revitalization after session expiry.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Auth Co {suffix}", owner_name="Owner", mobile_number=f"ac_{suffix}")
    db_session.add(company)
    await db_session.flush()

    user = User(
        company_id=company.id,
        full_name=f"User {suffix}",
        mobile_number=f"920{suffix}",
        password_hash=hash_password("UserPassword123!"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    expired_jti = secrets_jti = f"expired-jti-{suffix}"
    now = _utcnow()
    expired_session = AuthSession(
        user_id=user.id,
        company_id=company.id,
        session_jti=expired_jti,
        remember_me=False,
        expires_at=now - timedelta(minutes=10),  # Expired 10m ago
        revoked_at=None,
    )
    db_session.add(expired_session)
    await db_session.commit()

    # Create a refresh token signed with this JTI
    refresh_jwt = _create_refresh_token(user, jti=expired_jti, remember_me=False)

    # Attempting to refresh MUST raise HTTP 401 Unauthorized
    with pytest.raises(HTTPException) as exc_info:
        await refresh_access_token(refresh_jwt, db_session)

    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_refresh_token_revoked_session_rejected(db_session):
    """FG-SEC-054: A revoked AuthSession (revoked_at is not None) must NOT be refreshed."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Revoke Co {suffix}", owner_name="Owner", mobile_number=f"rc_{suffix}")
    db_session.add(company)
    await db_session.flush()

    user = User(
        company_id=company.id,
        full_name=f"Revoked User {suffix}",
        mobile_number=f"921{suffix}",
        password_hash=hash_password("UserPassword123!"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    revoked_jti = f"revoked-jti-{suffix}"
    now = _utcnow()
    revoked_session = AuthSession(
        user_id=user.id,
        company_id=company.id,
        session_jti=revoked_jti,
        remember_me=True,
        expires_at=now + timedelta(days=29),
        revoked_at=now - timedelta(minutes=5),  # Revoked
    )
    db_session.add(revoked_session)
    await db_session.commit()

    refresh_jwt = _create_refresh_token(user, jti=revoked_jti, remember_me=True)

    with pytest.raises(HTTPException) as exc_info:
        await refresh_access_token(refresh_jwt, db_session)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_valid_session_succeeds(db_session):
    """Verify an active, non-expired, non-revoked session successfully issues a new token."""
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Valid Co {suffix}", owner_name="Owner", mobile_number=f"vc_{suffix}")
    db_session.add(company)
    await db_session.flush()

    user = User(
        company_id=company.id,
        full_name=f"Valid User {suffix}",
        mobile_number=f"922{suffix}",
        password_hash=hash_password("UserPassword123!"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    valid_jti = f"valid-jti-{suffix}"
    now = _utcnow()
    valid_session = AuthSession(
        user_id=user.id,
        company_id=company.id,
        session_jti=valid_jti,
        remember_me=False,
        expires_at=now + timedelta(hours=12),
        revoked_at=None,
    )
    db_session.add(valid_session)
    await db_session.commit()

    refresh_jwt = _create_refresh_token(user, jti=valid_jti, remember_me=False)
    token_response = await refresh_access_token(refresh_jwt, db_session)

    assert token_response.access_token is not None
    assert token_response.token_type == "bearer"

    # Verify newly minted access token is bounded to 60m
    new_payload = decode_access_token(token_response.access_token)
    assert new_payload["sub"] == str(user.id)
    duration = new_payload["exp"] - new_payload.get("iat", int(now.timestamp()))
    assert 3500 <= duration <= 3660


# ==============================================================================
# 3. FG-SEC-055: Admin JWT JTI Tracking & Invalidation/Revocation
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_jwt_includes_jti_and_supports_revocation(db_session):
    """
    FG-SEC-055: Admin JWTs must include a unique JTI and be revocable
    via JTI or user-level token invalidation.
    """
    clear_admin_revocations_for_testing()
    suffix = uuid.uuid4().hex[:6]

    res = await db_session.execute(select(AdminRole).where(AdminRole.name == AdminRoleType.SUPER_ADMIN))
    role = res.scalar_one_or_none()
    if not role:
        role = AdminRole(name=AdminRoleType.SUPER_ADMIN, description="Super Administrator")
        db_session.add(role)
        await db_session.flush()

    admin = AdminUser(
        full_name=f"Admin {suffix}",
        email=f"admin_{suffix}@fleetguard.test",
        password_hash=hash_password("SuperSecretAdmin123!"),
        role_id=role.id,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Generate admin token
    token = create_admin_token(data={"admin_id": str(admin.id), "role": "SUPER_ADMIN"})
    payload = jwt.decode(token, get_admin_jwt_secret(), algorithms=[ADMIN_ALGORITHM])

    assert "jti" in payload, "Admin token missing jti claim"
    token_jti = payload["jti"]
    assert len(token_jti) >= 16

    # Verify token passes get_current_admin
    resolved_admin = await get_current_admin(token=token, db=db_session)
    assert resolved_admin.id == admin.id

    # Revoke token
    revoke_admin_token(token_jti)
    assert is_admin_token_revoked(token_jti) is True

    # After revocation, token MUST be rejected
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(token=token, db=db_session)
    assert exc_info.value.status_code == 401

    clear_admin_revocations_for_testing()


@pytest.mark.asyncio
async def test_admin_logout_endpoint_revokes_token(db_session):
    """FG-SEC-055: POST /api/v1/admin/auth/logout invalidates admin session immediately."""
    clear_admin_revocations_for_testing()
    suffix = uuid.uuid4().hex[:6]

    res = await db_session.execute(select(AdminRole).where(AdminRole.name == AdminRoleType.SUPER_ADMIN))
    role = res.scalar_one_or_none()
    if not role:
        role = AdminRole(name=AdminRoleType.SUPER_ADMIN, description="Super Administrator")
        db_session.add(role)
        await db_session.flush()

    admin = AdminUser(
        full_name=f"Logout Admin {suffix}",
        email=f"admin_logout_{suffix}@fleetguard.com",
        password_hash=hash_password("SuperSecretAdmin123!"),
        role_id=role.id,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    token = create_admin_token(data={"admin_id": str(admin.id), "role": "SUPER_ADMIN"})

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. /me succeeds before logout
            res_me = await client.get(
                "/api/v1/admin/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res_me.status_code == 200

            # 2. Call /logout
            res_logout = await client.post(
                "/api/v1/admin/auth/logout",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res_logout.status_code == 200
            assert res_logout.json().get("message") == "Admin session revoked successfully"

            # 3. /me fails after logout with HTTP 401
            res_me_after = await client.get(
                "/api/v1/admin/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res_me_after.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)
        clear_admin_revocations_for_testing()


# ==============================================================================
# 4. FG-SEC-051: Check-Then-Act Concurrency Lock on Maintenance Costs
# ==============================================================================

@pytest.mark.asyncio
async def test_maintenance_concurrency_lock_helper(db_session):
    """
    FG-SEC-051: Verify _get_locked_maintenance_record locks the record
    using with_for_update() and eagerly loads parts and labour collections.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Mnt Lock Co {suffix}", owner_name="Owner", mobile_number=f"ml_{suffix}")
    db_session.add(company)
    await db_session.flush()

    vehicle = Vehicle(company_id=company.id, registration_number=f"TRK-LCK-{suffix}", tank_capacity=200.0)
    db_session.add(vehicle)
    await db_session.flush()

    record = MaintenanceRecord(
        business_id=f"MNT-LCK-{suffix}",
        company_id=company.id,
        vehicle_id=vehicle.id,
        category=MaintenanceCategory.PREVENTIVE,
        status=MaintenanceStatus.STARTED,
        cost=1500.0,
        other_cost=500.0,
    )
    db_session.add(record)
    await db_session.commit()

    # Query using concurrency lock helper
    locked_record = await _get_locked_maintenance_record(db_session, record.id, company.id)
    assert locked_record is not None
    assert locked_record.id == record.id
    # Ensure parts and labour relations are loaded and accessible
    assert locked_record.parts == []
    assert locked_record.labour == []

    # Non-existent or cross-tenant record returns None
    other_tenant_record = await _get_locked_maintenance_record(db_session, record.id, company.id + 999)
    assert other_tenant_record is None


# ==============================================================================
# 5. FG-SEC-056: Double URL Prefix Cleanup (/api/v1/sos)
# ==============================================================================

def test_emergency_sos_routes_no_double_prefix():
    """
    FG-SEC-056: Ensure owner emergency SOS routes are mounted at /api/v1/sos/...
    and that no route exists with the double prefix /api/v1/v1/sos/...
    """
    route_paths = [r.path for r in app.routes if hasattr(r, "path")]

    # Assert correct normalized route exists
    assert "/api/v1/sos/active" in route_paths, (
        f"Expected '/api/v1/sos/active' in registered routes, found: {route_paths}"
    )
    assert "/api/v1/sos/{sos_id}/resolve" in route_paths, (
        f"Expected '/api/v1/sos/{{sos_id}}/resolve' in registered routes, found: {route_paths}"
    )

    # Assert NO double prefix routes exist
    double_prefix_routes = [p for p in route_paths if "/api/v1/v1/sos" in p or p.startswith("/api/v1/v1")]
    assert len(double_prefix_routes) == 0, (
        f"Detected lingering double prefix routes: {double_prefix_routes}"
    )


# ==============================================================================
# 6. FG-SEC-057: Deprecated In-Memory Fuel Shadow Mount Removal
# ==============================================================================

def test_in_memory_fuel_shadow_router_removed():
    """
    FG-SEC-057: Deprecated in-memory fuel repository shadow mount must be removed.
    Real fuel endpoints should resolve through database-backed repositories.
    """
    # Ensure domain.fuel.api is not in sys.modules or not mounted in app
    from domain.fuel.api import router as mock_fuel_router
    app_router_endpoints = [r.endpoint for r in app.routes if hasattr(r, "endpoint")]

    for mock_route in mock_fuel_router.routes:
        if hasattr(mock_route, "endpoint"):
            assert mock_route.endpoint not in app_router_endpoints, (
                f"In-memory fuel endpoint {mock_route.endpoint} is still registered in FastAPI app!"
            )
