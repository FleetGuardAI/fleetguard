"""
Integration and Unit Tests for Dual Login, QR Fleet Resolution, and Fleet Transfer Flows.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from main import app
from database import async_session_factory
import secrets
from models.auth_session import AuthSession
from models.company import Company, CompanyStatus
from models.user import User, UserRole
from models.driver_domain import Driver, DriverStatus, VerificationStatus
from models.fleet_invite import FleetInvite
from models.driver_fleet_transfer import DriverFleetTransfer, TransferStatus
from models.vehicle_domain import Vehicle
from utils.security import create_access_token, hash_password


async def create_user_token_with_session(session, user: User) -> str:
    jti = secrets.token_hex(16)
    auth_session = AuthSession(
        user_id=user.id,
        company_id=user.company_id,
        session_jti=jti,
        remember_me=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    session.add(auth_session)
    await session.commit()
    return create_access_token(
        data={
            "sub": str(user.id),
            "company_id": user.company_id,
            "role": user.role.value,
            "jti": jti,
        }
    )



@pytest.fixture(autouse=True)
def mock_otp_mode(monkeypatch):
    """Enable mock OTP mode for all tests."""
    from config import settings
    monkeypatch.setattr(settings, "OTP_MOCK_MODE", True)


@pytest.fixture
async def setup_test_companies():
    """Create two test fleet companies (Fleet A and Fleet B) and admin users."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]

        # Fleet A
        comp_a = Company(
            company_name=f"Fleet Alpha {uid}",
            owner_name="Owner A",
            mobile_number=f"9190000{uid[:4]}",
            status=CompanyStatus.ACTIVE,
        )
        session.add(comp_a)
        await session.flush()

        admin_a = User(
            company_id=comp_a.id,
            full_name="Admin Alpha",
            mobile_number=comp_a.mobile_number,
            password_hash=hash_password("password123"),
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
        )
        session.add(admin_a)

        # Fleet B
        comp_b = Company(
            company_name=f"Fleet Beta {uid}",
            owner_name="Owner B",
            mobile_number=f"9190001{uid[:4]}",
            status=CompanyStatus.ACTIVE,
        )
        session.add(comp_b)
        await session.flush()

        admin_b = User(
            company_id=comp_b.id,
            full_name="Admin Beta",
            mobile_number=comp_b.mobile_number,
            password_hash=hash_password("password123"),
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
        )
        session.add(admin_b)

        # Invites
        invite_a = FleetInvite(
            company_id=comp_a.id,
            invite_token=f"fg_invite_a_{uid}",
            is_active=True,
        )
        invite_b = FleetInvite(
            company_id=comp_b.id,
            invite_token=f"fg_invite_b_{uid}",
            is_active=True,
        )
        session.add_all([invite_a, invite_b])

        await session.commit()
        await session.refresh(comp_a)
        await session.refresh(comp_b)
        await session.refresh(invite_a)
        await session.refresh(invite_b)
        await session.refresh(admin_a)
        await session.refresh(admin_b)

        return {
            "comp_a": comp_a,
            "comp_b": comp_b,
            "invite_a": invite_a,
            "invite_b": invite_b,
            "admin_a": admin_a,
            "admin_b": admin_b,
            "uid": uid,
        }


@pytest.mark.asyncio
async def test_qr_resolve_unauthenticated(setup_test_companies):
    """Unauthenticated driver scans valid QR code -> prompt phone verification."""
    data = setup_test_companies
    invite_b = data["invite_b"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/driver-app/qr/resolve",
            json={"qr_data": f"fleetguard://invite?token={invite_b.invite_token}&company={invite_b.company_id}"}
        )
        assert response.status_code == 200
        res = response.json()
        assert res["valid"] is True
        assert res["action"] == "VERIFY_PHONE"
        assert res["company_id"] == invite_b.company_id
        assert res["company_name"] == data["comp_b"].company_name


@pytest.mark.asyncio
async def test_qr_resolve_same_fleet(setup_test_companies):
    """Case A: Existing driver scans their own fleet's QR -> LOGIN action."""
    data = setup_test_companies
    comp_a = data["comp_a"]
    invite_a = data["invite_a"]
    uid = data["uid"]

    # Create driver in Fleet A
    async with async_session_factory() as session:
        user_driver = User(
            company_id=comp_a.id,
            full_name="Driver Alpha One",
            mobile_number=f"9198700{uid[:4]}",
            password_hash=hash_password("pass"),
            role=UserRole.DRIVER,
            is_active=True,
        )
        session.add(user_driver)
        await session.flush()

        driver = Driver(
            name="Driver Alpha One",
            phone_number=user_driver.mobile_number,
            company_id=comp_a.id,
            user_id=user_driver.id,
            status=DriverStatus.ACTIVE,
            verification_status=VerificationStatus.APPROVED,
        )
        session.add(driver)
        await session.commit()
        await session.refresh(driver)
        token = await create_user_token_with_session(session, user_driver)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/driver-app/qr/resolve",
            headers={"Authorization": f"Bearer {token}"},
            json={"qr_data": invite_a.invite_token}
        )
        assert response.status_code == 200
        res = response.json()
        assert res["valid"] is True
        assert res["action"] == "LOGIN"
        assert res["is_same_fleet"] is True
        assert res["is_fleet_mismatch"] is False


@pytest.mark.asyncio
async def test_qr_resolve_fleet_mismatch(setup_test_companies):
    """Case B: Driver of Fleet A scans Fleet B's QR -> CONFIRM_SWITCH action."""
    data = setup_test_companies
    comp_a = data["comp_a"]
    comp_b = data["comp_b"]
    invite_b = data["invite_b"]
    uid = data["uid"]

    async with async_session_factory() as session:
        user_driver = User(
            company_id=comp_a.id,
            full_name="Driver Alpha Two",
            mobile_number=f"9198701{uid[:4]}",
            password_hash=hash_password("pass"),
            role=UserRole.DRIVER,
            is_active=True,
        )
        session.add(user_driver)
        await session.flush()

        driver = Driver(
            name="Driver Alpha Two",
            phone_number=user_driver.mobile_number,
            company_id=comp_a.id,
            user_id=user_driver.id,
            status=DriverStatus.ACTIVE,
            verification_status=VerificationStatus.APPROVED,
        )
        session.add(driver)
        await session.commit()
        await session.refresh(driver)
        token = await create_user_token_with_session(session, user_driver)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/driver-app/qr/resolve",
            headers={"Authorization": f"Bearer {token}"},
            json={"qr_data": invite_b.invite_token}
        )
        assert response.status_code == 200
        res = response.json()
        assert res["valid"] is True
        assert res["action"] == "CONFIRM_SWITCH"
        assert res["is_same_fleet"] is False
        assert res["is_fleet_mismatch"] is True
        assert res["current_company_id"] == comp_a.id
        assert res["target_company_id"] == comp_b.id


@pytest.mark.asyncio
async def test_verify_otp_direct_mobile_login(setup_test_companies):
    """Driver logs in directly with mobile number (no QR invite) -> logs in to their fleet."""
    data = setup_test_companies
    comp_a = data["comp_a"]
    uid = data["uid"]
    phone = f"9198702{uid[:4]}"

    async with async_session_factory() as session:
        user_driver = User(
            company_id=comp_a.id,
            full_name="Driver Direct",
            mobile_number=phone,
            password_hash=hash_password("pass"),
            role=UserRole.DRIVER,
            is_active=True,
        )
        session.add(user_driver)
        await session.flush()

        driver = Driver(
            name="Driver Direct",
            phone_number=phone,
            company_id=comp_a.id,
            user_id=user_driver.id,
            status=DriverStatus.ACTIVE,
            verification_status=VerificationStatus.APPROVED,
        )
        session.add(driver)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Request OTP
        send_res = await ac.post("/api/v1/driver-app/send-otp", json={"phone_number": phone})
        assert send_res.status_code == 200
        req_id = send_res.json()["req_id"]

        # Verify OTP directly (no invite_token)
        verify_res = await ac.post(
            "/api/v1/driver-app/verify-otp",
            json={
                "phone_number": phone,
                "req_id": req_id,
                "otp_code": "123456",
            }
        )
        assert verify_res.status_code == 200
        vres = verify_res.json()
        assert vres["is_new_driver"] is False
        assert vres["company_id"] == comp_a.id
        assert vres["is_fleet_mismatch"] is False
        assert vres["verification_status"] == "APPROVED"


@pytest.mark.asyncio
async def test_fleet_transfer_and_admin_approval_flow(setup_test_companies):
    """Complete end-to-end fleet transfer request and admin approval."""
    data = setup_test_companies
    comp_a = data["comp_a"]
    comp_b = data["comp_b"]
    invite_b = data["invite_b"]
    admin_b = data["admin_b"]
    uid = data["uid"]
    phone = f"9198703{uid[:4]}"

    # Setup driver in Fleet A assigned to Vehicle A
    async with async_session_factory() as session:
        user_driver = User(
            company_id=comp_a.id,
            full_name="Driver Transfer Flow",
            mobile_number=phone,
            password_hash=hash_password("pass"),
            role=UserRole.DRIVER,
            is_active=True,
        )
        session.add(user_driver)
        await session.flush()

        driver = Driver(
            name="Driver Transfer Flow",
            phone_number=phone,
            company_id=comp_a.id,
            user_id=user_driver.id,
            status=DriverStatus.ACTIVE,
            verification_status=VerificationStatus.APPROVED,
        )
        session.add(driver)
        await session.flush()

        vehicle = Vehicle(
            company_id=comp_a.id,
            registration_number=f"DL01AB{uid[:4]}",
            assigned_driver_id=driver.id,
        )
        session.add(vehicle)
        await session.commit()
        await session.refresh(driver)
        await session.refresh(vehicle)
        driver_id = driver.id
        vehicle_id = vehicle.id
        driver_token = await create_user_token_with_session(session, user_driver)
        admin_b_token = await create_user_token_with_session(session, admin_b)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Driver initiates transfer to Fleet B
        trans_res = await ac.post(
            "/api/v1/driver-app/fleet-transfer",
            headers={"Authorization": f"Bearer {driver_token}"},
            json={
                "invite_token": invite_b.invite_token,
                "target_company_id": comp_b.id,
            }
        )
        assert trans_res.status_code == 200
        transfer_data = trans_res.json()
        assert transfer_data["status"] == "PENDING_APPROVAL"
        transfer_id = transfer_data["id"]

        # Verify driver is STILL in Fleet A while transfer is pending
        async with async_session_factory() as session:
            d_check = await session.get(Driver, driver_id)
            assert d_check.company_id == comp_a.id

        # 2. Admin of Fleet B views incoming transfers
        list_res = await ac.get(
            "/api/v1/drivers/fleet-transfers",
            headers={"Authorization": f"Bearer {admin_b_token}"}
        )
        assert list_res.status_code == 200
        transfers_list = list_res.json()
        assert any(t["id"] == transfer_id for t in transfers_list)

        # 3. Admin of Fleet B approves the transfer
        approve_res = await ac.post(
            f"/api/v1/drivers/fleet-transfers/{transfer_id}/approve",
            headers={"Authorization": f"Bearer {admin_b_token}"}
        )
        assert approve_res.status_code == 200

        # 4. Verify post-approval state
        async with async_session_factory() as session:
            # Transfer record is APPROVED
            t_check = await session.get(DriverFleetTransfer, transfer_id)
            assert t_check.status == TransferStatus.APPROVED

            # Driver is now in Fleet B
            d_check = await session.get(Driver, driver_id)
            assert d_check.company_id == comp_b.id
            assert d_check.status == DriverStatus.ACTIVE

            # Old vehicle in Fleet A is unassigned
            v_check = await session.get(Vehicle, vehicle_id)
            assert v_check.assigned_driver_id is None
