import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from models.company import Company, CompanyStatus
from models.vehicle_domain import Vehicle
from models.fuel_domain import FuelTransaction, FuelTransactionType
from models.auth_session import AuthSession
from utils.security import create_access_token, hash_password


def create_token(user: User, db_session: AsyncSession) -> str:
    jti = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    session = AuthSession(
        session_jti=jti,
        user_id=user.id,
        company_id=user.company_id,
        remember_me=False,
        expires_at=now + timedelta(days=1),
    )
    db_session.add(session)
    token_data = {
        "sub": str(user.id),
        "jti": jti,
        "company_id": user.company_id,
        "role": user.role.value,
        "type": "access",
    }
    return create_access_token(token_data)


def test_unauthenticated_fuel_transaction_rejected(client: TestClient):
    """FG-SEC-004: Unauthenticated access to fuel transactions returns 401."""
    resp = client.get("/api/v1/fuel/1")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_fuel_transaction_tenant_isolation(client: TestClient, db_session: AsyncSession):
    """
    FG-SEC-004: Same-company user can read fuel transaction;
    cross-tenant user receives 404 (preventing data leakage and ID enumeration).
    """
    uid1 = uuid.uuid4().hex[:6]
    uid2 = uuid.uuid4().hex[:6]

    # Company 1
    comp1 = Company(
        company_name=f"Fuel Tenant 1 {uid1}",
        owner_name="Owner 1",
        mobile_number=f"+9198{uid1[:8]}",
        status=CompanyStatus.ACTIVE,
    )
    db_session.add(comp1)
    await db_session.flush()

    # Company 2
    comp2 = Company(
        company_name=f"Fuel Tenant 2 {uid2}",
        owner_name="Owner 2",
        mobile_number=f"+9197{uid2[:8]}",
        status=CompanyStatus.ACTIVE,
    )
    db_session.add(comp2)
    await db_session.flush()

    # User 1 (Company 1)
    user1 = User(
        company_id=comp1.id,
        full_name="User 1",
        mobile_number=f"+9191{uid1[:8]}",
        password_hash=hash_password("password"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    db_session.add(user1)

    # User 2 (Company 2)
    user2 = User(
        company_id=comp2.id,
        full_name="User 2",
        mobile_number=f"+9192{uid2[:8]}",
        password_hash=hash_password("password"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    db_session.add(user2)
    await db_session.flush()

    token1 = create_token(user1, db_session)
    token2 = create_token(user2, db_session)
    await db_session.flush()

    # Vehicle in Company 1
    vehicle1 = Vehicle(
        company_id=comp1.id,
        registration_number=f"MH{uid1[:4].upper()}1",
        tank_capacity=100.0,
    )
    db_session.add(vehicle1)
    await db_session.flush()

    # FuelTransaction in Company 1
    tx1 = FuelTransaction(
        company_id=comp1.id,
        vehicle_id=vehicle1.id,
        transaction_type=FuelTransactionType.FILL,
        amount_liters=50.0,
        price_per_liter=95.0,
        total_cost=4750.0,
        fuel_type="DIESEL",
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(tx1)
    await db_session.flush()

    # 1. Company 1 user requesting Company 1 transaction -> 200
    headers1 = {"Authorization": f"Bearer {token1}"}
    resp1 = client.get(f"/api/v1/fuel/{tx1.id}", headers=headers1)
    assert resp1.status_code == 200, resp1.text
    data1 = resp1.json()
    assert data1["id"] == tx1.id
    assert data1["company_id"] == comp1.id

    # 2. Company 2 user requesting Company 1 transaction -> 404
    headers2 = {"Authorization": f"Bearer {token2}"}
    resp2 = client.get(f"/api/v1/fuel/{tx1.id}", headers=headers2)
    assert resp2.status_code == 404

    # 3. Direct repository mandatory scoping check:
    from repositories.fuel_repository import FuelRepository
    repo = FuelRepository(db_session)
    with pytest.raises(ValueError, match="company_id is mandatory"):
        await repo.get_transaction_by_id(tx1.id, company_id=None)

    # 4. Explicit unscoped access works via dedicated privileged method:
    unscoped_tx = await repo.get_transaction_by_id_unscoped(tx1.id)
    assert unscoped_tx is not None
    assert unscoped_tx.id == tx1.id


@pytest.mark.asyncio
async def test_super_admin_unscoped_fuel_access(client: TestClient, db_session: AsyncSession):
    """
    FG-SEC-004 & FG-SEC-003 (Batch 1.3): Super Admin Authentication Separation.
    1. Ordinary company users (Company Admin, Fleet Manager, Dispatcher, Driver)
       cannot access cross-tenant fuel transactions (404).
    2. A normal company user cannot obtain unscoped platform-wide access merely by
       manipulating a role claim to 'SUPER_ADMIN' (404).
    3. Invalid admin tokens are rejected (401).
    4. Valid dedicated platform administrator (AdminUser authenticated with ADMIN_JWT_SECRET)
       can access unscoped operations.
    """
    from models.admin_domain import AdminUser, AdminRole, AdminRoleType
    from services.admin_auth_service import create_access_token as create_admin_jwt
    from sqlalchemy import select

    uid1 = uuid.uuid4().hex[:6]
    uid2 = uuid.uuid4().hex[:6]

    comp1 = Company(
        company_name=f"Fuel Tenant A {uid1}",
        owner_name="Owner A",
        mobile_number=f"+9196{uid1[:8]}",
        status=CompanyStatus.ACTIVE,
    )
    comp2 = Company(
        company_name=f"Fuel Tenant B {uid2}",
        owner_name="Owner B",
        mobile_number=f"+9195{uid2[:8]}",
        status=CompanyStatus.ACTIVE,
    )
    db_session.add_all([comp1, comp2])
    await db_session.flush()

    # 1. Company Admin in Tenant 2
    company_admin = User(
        company_id=comp2.id,
        full_name="Company Admin B",
        mobile_number=f"+9194{uid2[:8]}",
        password_hash=hash_password("password"),
        role=UserRole.COMPANY_ADMIN,
        is_active=True,
    )
    # 2. Fleet Manager in Tenant 2
    fleet_manager = User(
        company_id=comp2.id,
        full_name="Fleet Manager B",
        mobile_number=f"+9193{uid2[:8]}",
        password_hash=hash_password("password"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    # 3. Driver in Tenant 2
    driver_user = User(
        company_id=comp2.id,
        full_name="Driver B",
        mobile_number=f"+9192{uid2[:8]}",
        password_hash=hash_password("password"),
        role=UserRole.DRIVER,
        is_active=True,
    )
    # 4. Ordinary User in Tenant 2 with forged/assigned SUPER_ADMIN role on tenant token
    tampered_user = User(
        company_id=comp2.id,
        full_name="Tampered User",
        mobile_number=f"+9191{uid2[:8]}",
        password_hash=hash_password("password"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    db_session.add_all([company_admin, fleet_manager, driver_user, tampered_user])
    await db_session.flush()

    token_ca = create_token(company_admin, db_session)
    token_fm = create_token(fleet_manager, db_session)
    token_dr = create_token(driver_user, db_session)
    token_tampered = create_token(tampered_user, db_session)

    # 5. Dedicated Platform AdminUser (platform administrator domain)
    res = await db_session.execute(select(AdminRole).where(AdminRole.name == AdminRoleType.SUPER_ADMIN))
    admin_role = res.scalar_one_or_none()
    if not admin_role:
        admin_role = AdminRole(name=AdminRoleType.SUPER_ADMIN, description="Platform Super Admin")
        db_session.add(admin_role)
        await db_session.flush()

    platform_admin = AdminUser(
        email=f"platform_admin_{uid1}@fleetguard.com",
        full_name="Platform Administrator",
        password_hash=hash_password("admin_secret_pass"),
        role_id=admin_role.id,
        is_active=True,
    )
    db_session.add(platform_admin)
    await db_session.flush()

    token_platform_admin = create_admin_jwt({"admin_id": str(platform_admin.id)})

    # Target Vehicle and Transaction in Company 1
    vehicle1 = Vehicle(
        company_id=comp1.id,
        registration_number=f"MH{uid1[:4].upper()}2",
        tank_capacity=80.0,
    )
    db_session.add(vehicle1)
    await db_session.flush()

    tx1 = FuelTransaction(
        company_id=comp1.id,
        vehicle_id=vehicle1.id,
        transaction_type=FuelTransactionType.FILL,
        amount_liters=40.0,
        price_per_liter=92.0,
        total_cost=3680.0,
        fuel_type="DIESEL",
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(tx1)
    await db_session.flush()

    # Test A: Company Admin of Tenant 2 receives 404
    resp = client.get(f"/api/v1/fuel/{tx1.id}", headers={"Authorization": f"Bearer {token_ca}"})
    assert resp.status_code == 404

    # Test B: Fleet Manager of Tenant 2 receives 404
    resp = client.get(f"/api/v1/fuel/{tx1.id}", headers={"Authorization": f"Bearer {token_fm}"})
    assert resp.status_code == 404

    # Test C: Driver of Tenant 2 receives 404
    resp = client.get(f"/api/v1/fuel/{tx1.id}", headers={"Authorization": f"Bearer {token_dr}"})
    assert resp.status_code == 404

    # Test D: Tampered User with SUPER_ADMIN role claim receives 404 (cannot bypass tenant scoping)
    resp = client.get(f"/api/v1/fuel/{tx1.id}", headers={"Authorization": f"Bearer {token_tampered}"})
    assert resp.status_code == 404

    # Test E: Invalid / malformed admin token receives 401
    resp = client.get(f"/api/v1/fuel/{tx1.id}", headers={"Authorization": "Bearer invalid_admin_jwt_token"})
    assert resp.status_code == 401

    # Test F: Valid dedicated platform administrator receives 200 via /api/v1/fuel/{id}
    resp_admin = client.get(f"/api/v1/fuel/{tx1.id}", headers={"Authorization": f"Bearer {token_platform_admin}"})
    assert resp_admin.status_code == 200
    assert resp_admin.json()["id"] == tx1.id
    assert resp_admin.json()["company_id"] == comp1.id

    # Test G: Valid dedicated platform administrator receives 200 via /api/v1/admin/fuel/{id}
    resp_admin_route = client.get(f"/api/v1/admin/fuel/{tx1.id}", headers={"Authorization": f"Bearer {token_platform_admin}"})
    assert resp_admin_route.status_code == 200
    assert resp_admin_route.json()["id"] == tx1.id
