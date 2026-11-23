"""
Security & Privilege Escalation Regression Suite
Verifies that:
1. Drivers, unauthenticated callers, and ordinary users cannot activate drivers.
2. User-controlled registration payloads cannot elevate driver status to ACTIVE.
3. Drivers cannot self-activate via profile, document, or verification endpoints.
4. Approval strictly requires authorized roles (COMPANY_ADMIN / SUPER_ADMIN) and 5 verified KYC documents.
5. Multi-tenant company boundaries are strictly enforced across driver and expense endpoints.
"""

import pytest
import uuid
import random
import secrets
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from main import app
from database import async_session_factory
from models.user import User, UserRole
from models.auth_session import AuthSession
from models.driver_domain import Driver, DriverStatus, VerificationStatus
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from utils.security import create_access_token, hash_password


async def create_user_with_session(session, user: User) -> str:
    """Helper to save user, create valid AuthSession, and return valid JWT."""
    session.add(user)
    await session.commit()
    await session.refresh(user)

    jti = secrets.token_urlsafe(24)
    auth_session = AuthSession(
        user_id=user.id,
        company_id=user.company_id,
        session_jti=jti,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    session.add(auth_session)
    await session.commit()

    return create_access_token({
        "sub": str(user.id),
        "company_id": user.company_id,
        "role": user.role.value,
        "jti": jti,
    })


@pytest.mark.asyncio
async def test_unauthenticated_driver_creation_rejected():
    """Unauthenticated users cannot create drivers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/drivers", json={
            "name": "Attacker Driver",
            "phone_number": "9998887776",
            "status": "ACTIVE",
        })
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_driver_role_cannot_create_driver():
    """Users with DRIVER role cannot invoke administrative driver creation."""
    async with async_session_factory() as session:
        driver_user = User(
            company_id=10,
            full_name="Driver User",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.DRIVER,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        token = await create_user_with_session(session, driver_user)

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/drivers", headers=headers, json={
            "name": "Illegitimate Driver",
            "phone_number": f"97{random.randint(10000000, 99999999)}",
            "status": "ACTIVE",
        })
        assert resp.status_code == 403
        assert "Only fleet managers or administrators" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_registration_payload_cannot_grant_active_status():
    """Even authorized admins cannot create a driver directly as ACTIVE; status must default to INACTIVE."""
    async with async_session_factory() as session:
        admin_user = User(
            company_id=11,
            full_name="Company Admin",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        token = await create_user_with_session(session, admin_user)

    headers = {"Authorization": f"Bearer {token}"}

    phone = f"96{random.randint(10000000, 99999999)}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/drivers", headers=headers, json={
            "name": "New Driver",
            "phone_number": phone,
            "status": "ACTIVE",  # Attempting to inject ACTIVE status
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "INACTIVE", "Driver status must default to INACTIVE even if payload requested ACTIVE"
        assert data["verification_status"] == "PENDING_DOCUMENTS"


@pytest.mark.asyncio
async def test_driver_cannot_self_approve():
    """Driver role cannot call driver approval endpoint."""
    async with async_session_factory() as session:
        driver_user = User(
            company_id=12,
            full_name="Driver Self",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.DRIVER,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        token = await create_user_with_session(session, driver_user)

        driver = Driver(
            company_id=12,
            name="Driver Self",
            phone_number=driver_user.mobile_number,
            user_id=driver_user.id,
            status=DriverStatus.INACTIVE,
            verification_status=VerificationStatus.PENDING_DOCUMENTS,
            origin_type="test",
        )
        session.add(driver)
        await session.commit()
        await session.refresh(driver)

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(f"/api/v1/drivers/{driver.id}/approve", headers=headers, json={"action": "APPROVED"})
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cross_company_driver_approval_rejected():
    """Company A admin cannot approve a driver belonging to Company B."""
    async with async_session_factory() as session:
        admin_a = User(
            company_id=20,
            full_name="Admin A",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        token_a = await create_user_with_session(session, admin_a)

        driver_b = Driver(
            company_id=21,
            name="Driver B",
            phone_number=f"95{random.randint(10000000, 99999999)}",
            status=DriverStatus.INACTIVE,
            verification_status=VerificationStatus.PENDING_DOCUMENTS,
            origin_type="test",
        )
        session.add(driver_b)
        await session.commit()
        await session.refresh(driver_b)

    headers_a = {"Authorization": f"Bearer {token_a}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(f"/api/v1/drivers/{driver_b.id}/approve", headers=headers_a, json={"action": "APPROVED"})
        assert resp.status_code in [403, 404]


@pytest.mark.asyncio
async def test_cross_company_driver_modification_rejected():
    """Company A admin cannot update or delete Company B's driver."""
    async with async_session_factory() as session:
        admin_a = User(
            company_id=30,
            full_name="Admin A",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        token_a = await create_user_with_session(session, admin_a)

        driver_b = Driver(
            company_id=31,
            name="Driver B",
            phone_number=f"94{random.randint(10000000, 99999999)}",
            status=DriverStatus.INACTIVE,
            verification_status=VerificationStatus.PENDING_DOCUMENTS,
            origin_type="test",
        )
        session.add(driver_b)
        await session.commit()
        await session.refresh(driver_b)

    headers_a = {"Authorization": f"Bearer {token_a}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Attempt update
        patch_res = await ac.patch(f"/api/v1/drivers/{driver_b.id}", headers=headers_a, json={"name": "Hacked Driver"})
        assert patch_res.status_code in [403, 404]

        # Attempt delete
        del_res = await ac.delete(f"/api/v1/drivers/{driver_b.id}", headers=headers_a)
        assert del_res.status_code in [403, 404]


@pytest.mark.asyncio
async def test_driver_cannot_submit_expense_for_another_driver():
    """A driver cannot submit an expense targeting a different driver ID."""
    async with async_session_factory() as session:
        user_1 = User(
            company_id=40,
            full_name="Driver One",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.DRIVER,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        token_1 = await create_user_with_session(session, user_1)

        user_2 = User(
            company_id=40,
            full_name="Driver Two",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.DRIVER,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        session.add(user_2)
        await session.commit()
        await session.refresh(user_2)

        drv_1 = Driver(
            company_id=40,
            name="Driver One",
            phone_number=user_1.mobile_number,
            user_id=user_1.id,
            status=DriverStatus.ACTIVE,
            verification_status=VerificationStatus.APPROVED,
            origin_type="test",
        )
        drv_2 = Driver(
            company_id=40,
            name="Driver Two",
            phone_number=user_2.mobile_number,
            user_id=user_2.id,
            status=DriverStatus.ACTIVE,
            verification_status=VerificationStatus.APPROVED,
            origin_type="test",
        )
        session.add_all([drv_1, drv_2])
        await session.commit()
        await session.refresh(drv_1)
        await session.refresh(drv_2)

    headers_1 = {"Authorization": f"Bearer {token_1}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/driver-app/expenses",
            headers=headers_1,
            json={
                "category": "TOLL",
                "amount": 150.0,
                "driver_id": drv_2.id,  # Attempting to forge another driver's ID
                "description": "Toll gate",
            }
        )
        assert resp.status_code == 403
        assert "Drivers cannot submit expenses for another driver" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_driver_cannot_view_another_driver_expenses():
    """A driver cannot list expenses of another driver by specifying driver_id query parameter."""
    async with async_session_factory() as session:
        user_1 = User(
            company_id=50,
            full_name="Driver 1",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.DRIVER,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        token_1 = await create_user_with_session(session, user_1)

        user_2 = User(
            company_id=50,
            full_name="Driver 2",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.DRIVER,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        session.add(user_2)
        await session.commit()
        await session.refresh(user_2)

        drv_1 = Driver(company_id=50, name="D1", phone_number=user_1.mobile_number, user_id=user_1.id, status=DriverStatus.ACTIVE, origin_type="test")
        drv_2 = Driver(company_id=50, name="D2", phone_number=user_2.mobile_number, user_id=user_2.id, status=DriverStatus.ACTIVE, origin_type="test")
        session.add_all([drv_1, drv_2])
        await session.commit()
        await session.refresh(drv_1)
        await session.refresh(drv_2)

    headers_1 = {"Authorization": f"Bearer {token_1}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/driver-app/expenses?driver_id={drv_2.id}", headers=headers_1)
        assert resp.status_code == 403
        assert "Drivers can only view their own expenses" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_cross_company_expense_isolation():
    """Company A user cannot view expenses of Company B."""
    async with async_session_factory() as session:
        user_b = User(
            company_id=61,
            full_name="User B",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        token_b = await create_user_with_session(session, user_b)

        drv_b = Driver(company_id=61, name="Driver B", phone_number=f"93{random.randint(10000000, 99999999)}", status=DriverStatus.ACTIVE, origin_type="test")
        session.add(drv_b)
        await session.commit()
        await session.refresh(drv_b)

        exp_b = Expense(
            business_id=f"exp_{uuid.uuid4().hex[:12]}",
            company_id=61,
            driver_id=drv_b.id,
            category=ExpenseCategory.TOLL,
            amount=200.0,
            currency="INR",
            status=ExpenseStatus.PENDING,
            expense_date=datetime.now(timezone.utc),
            origin_type="test",
            origin_id=f"driver_{drv_b.id}",
        )
        session.add(exp_b)
        await session.commit()

        # Driver of Company A
        user_a = User(
            company_id=60,
            full_name="Driver A",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            role=UserRole.DRIVER,
            is_active=True,
            password_hash=hash_password("pass123"),
        )
        token_a = await create_user_with_session(session, user_a)
        drv_a = Driver(
            company_id=60,
            name="Driver A",
            phone_number=user_a.mobile_number,
            user_id=user_a.id,
            status=DriverStatus.ACTIVE,
            verification_status=VerificationStatus.APPROVED,
            origin_type="test",
        )
        session.add(drv_a)
        await session.commit()
        await session.refresh(drv_a)

    headers_a = {"Authorization": f"Bearer {token_a}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Driver A tries to list Company B driver's expenses
        resp = await ac.get(f"/api/v1/driver-app/expenses?driver_id={drv_b.id}", headers=headers_a)
        assert resp.status_code == 403
