import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from models.company import Company, CompanyStatus
from models.driver_domain import Driver
from models.emergency import EmergencyAlert, EmergencyStatus
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


def test_unauthenticated_sos_active_rejected(client: TestClient):
    """FG-SEC-005: Unauthenticated access to active SOS alerts returns 401."""
    resp = client.get("/api/v1/driver-app/sos/active?company_id=1")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_driver_sos_tenant_isolation(client: TestClient, db_session: AsyncSession):
    """
    FG-SEC-005:
    - Company 1 manager receives Company 1 alerts.
    - Company 2 manager specifying Company 1 is rejected with 403 Forbidden.
    - Company 2 manager without param receives only Company 2 alerts.
    """
    uid1 = uuid.uuid4().hex[:6]
    uid2 = uuid.uuid4().hex[:6]

    # Company 1
    comp1 = Company(
        company_name=f"SOS Co 1 {uid1}",
        owner_name="Owner 1",
        mobile_number=f"+9198{uid1[:8]}",
        status=CompanyStatus.ACTIVE,
    )
    db_session.add(comp1)

    # Company 2
    comp2 = Company(
        company_name=f"SOS Co 2 {uid2}",
        owner_name="Owner 2",
        mobile_number=f"+9197{uid2[:8]}",
        status=CompanyStatus.ACTIVE,
    )
    db_session.add(comp2)
    await db_session.flush()

    # Manager 1 (Co 1)
    mgr1 = User(
        company_id=comp1.id,
        full_name="Manager 1",
        mobile_number=f"+9191{uid1[:8]}",
        password_hash=hash_password("password"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    db_session.add(mgr1)

    # Manager 2 (Co 2)
    mgr2 = User(
        company_id=comp2.id,
        full_name="Manager 2",
        mobile_number=f"+9192{uid2[:8]}",
        password_hash=hash_password("password"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    db_session.add(mgr2)

    # Driver 1 (Co 1)
    driver_user1 = User(
        company_id=comp1.id,
        full_name="Driver User 1",
        mobile_number=f"+9193{uid1[:8]}",
        password_hash=hash_password("password"),
        role=UserRole.DRIVER,
        is_active=True,
    )
    db_session.add(driver_user1)
    await db_session.flush()

    driver1 = Driver(
        company_id=comp1.id,
        user_id=driver_user1.id,
        name="Driver One",
        phone_number=driver_user1.mobile_number,
    )
    db_session.add(driver1)
    await db_session.flush()

    token_mgr1 = create_token(mgr1, db_session)
    token_mgr2 = create_token(mgr2, db_session)
    token_drv1 = create_token(driver_user1, db_session)

    # Create active SOS for Driver 1 in Company 1
    sos1 = EmergencyAlert(
        driver_id=driver1.id,
        company_id=comp1.id,
        latitude=19.0760,
        longitude=72.8777,
        status=EmergencyStatus.ACTIVE,
        message="Vehicle breakdown distress",
    )
    db_session.add(sos1)
    await db_session.flush()

    # 1. Manager 1 sees SOS 1
    resp1 = client.get("/api/v1/driver-app/sos/active", headers={"Authorization": f"Bearer {token_mgr1}"})
    assert resp1.status_code == 200, resp1.text
    items1 = resp1.json()
    assert len(items1) == 1
    assert items1[0]["id"] == sos1.id

    # 2. Manager 2 attempts to request Company 1 alerts -> 403 Forbidden
    resp2_cross = client.get(
        f"/api/v1/driver-app/sos/active?company_id={comp1.id}",
        headers={"Authorization": f"Bearer {token_mgr2}"}
    )
    assert resp2_cross.status_code == 403

    # 3. Manager 2 without company_id -> sees 0 alerts
    resp2_own = client.get(
        "/api/v1/driver-app/sos/active",
        headers={"Authorization": f"Bearer {token_mgr2}"}
    )
    assert resp2_own.status_code == 200
    assert len(resp2_own.json()) == 0

    # 4. Driver 1 sees own alert
    resp_drv = client.get(
        "/api/v1/driver-app/sos/active",
        headers={"Authorization": f"Bearer {token_drv1}"}
    )
    assert resp_drv.status_code == 200
    assert len(resp_drv.json()) == 1
    assert resp_drv.json()[0]["id"] == sos1.id
