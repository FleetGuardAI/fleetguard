import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from models.user import User, UserRole
from models.company import Company, CompanyStatus
from models.auth_session import AuthSession
from models.driver_domain import Driver
from utils.security import create_access_token, hash_password


@pytest_asyncio.fixture
async def ws_test_setup(db_session: AsyncSession):
    """Setup companies, users, drivers, and auth sessions for WebSocket testing."""
    uid = uuid.uuid4().hex[:6]

    # Company 1
    company1 = Company(
        company_name=f"WS Test Co 1 {uid}",
        owner_name="Owner 1",
        mobile_number=f"+9198{uid[:8]}",
        email=f"owner1_{uid}@test.com",
        status=CompanyStatus.ACTIVE,
    )
    db_session.add(company1)
    await db_session.flush()

    # Company 2
    company2 = Company(
        company_name=f"WS Test Co 2 {uid}",
        owner_name="Owner 2",
        mobile_number=f"+9197{uid[:8]}",
        email=f"owner2_{uid}@test.com",
        status=CompanyStatus.ACTIVE,
    )
    db_session.add(company2)
    await db_session.flush()

    # Manager in Company 1
    manager1 = User(
        company_id=company1.id,
        full_name="Manager 1",
        email=f"manager1_{uid}@test.com",
        mobile_number=f"+9191{uid[:8]}",
        password_hash=hash_password("password123"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    db_session.add(manager1)

    # Manager in Company 2
    manager2 = User(
        company_id=company2.id,
        full_name="Manager 2",
        email=f"manager2_{uid}@test.com",
        mobile_number=f"+9192{uid[:8]}",
        password_hash=hash_password("password123"),
        role=UserRole.FLEET_MANAGER,
        is_active=True,
    )
    db_session.add(manager2)

    # Driver User 1 in Company 1
    driver_user1 = User(
        company_id=company1.id,
        full_name="Driver User 1",
        email=f"driveruser1_{uid}@test.com",
        mobile_number=f"+9193{uid[:8]}",
        password_hash=hash_password("password123"),
        role=UserRole.DRIVER,
        is_active=True,
    )
    db_session.add(driver_user1)

    # Driver User 2 in Company 1
    driver_user2 = User(
        company_id=company1.id,
        full_name="Driver User 2",
        email=f"driveruser2_{uid}@test.com",
        mobile_number=f"+9194{uid[:8]}",
        password_hash=hash_password("password123"),
        role=UserRole.DRIVER,
        is_active=True,
    )
    db_session.add(driver_user2)
    await db_session.flush()

    # Driver profile 1
    driver1 = Driver(
        company_id=company1.id,
        user_id=driver_user1.id,
        name="Driver One",
        phone_number=driver_user1.mobile_number,
    )
    db_session.add(driver1)

    # Driver profile 2
    driver2 = Driver(
        company_id=company1.id,
        user_id=driver_user2.id,
        name="Driver Two",
        phone_number=driver_user2.mobile_number,
    )
    db_session.add(driver2)
    await db_session.flush()

    # Helper function to generate valid tokens with active sessions
    async def create_user_token(user: User, is_expired: bool = False, is_revoked: bool = False) -> str:
        jti = uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        expires_at = now - timedelta(hours=1) if is_expired else now + timedelta(days=1)
        revoked_at = now if is_revoked else None

        session = AuthSession(
            session_jti=jti,
            user_id=user.id,
            company_id=user.company_id,
            remember_me=False,
            expires_at=expires_at,
            revoked_at=revoked_at,
        )
        db_session.add(session)
        await db_session.flush()

        token_data = {
            "sub": str(user.id),
            "jti": jti,
            "company_id": user.company_id,
            "role": user.role.value,
            "type": "access",
        }
        expires_delta = timedelta(hours=-1) if is_expired else timedelta(days=1)
        return create_access_token(token_data, expires_delta=expires_delta)

    return {
        "company1": company1,
        "company2": company2,
        "manager1": manager1,
        "manager2": manager2,
        "driver_user1": driver_user1,
        "driver_user2": driver_user2,
        "driver1": driver1,
        "driver2": driver2,
        "create_user_token": create_user_token,
    }


@pytest.mark.asyncio
async def test_ws_fleet_missing_token(client: TestClient, ws_test_setup):
    """Test that missing token rejects the WebSocket connection."""
    cid = ws_test_setup["company1"].id
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/fleet/{cid}") as ws:
            ws.receive_text()


@pytest.mark.asyncio
async def test_ws_fleet_invalid_token(client: TestClient, ws_test_setup):
    """Test that invalid/malformed token rejects connection."""
    cid = ws_test_setup["company1"].id
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/fleet/{cid}?token=invalid.jwt.token") as ws:
            ws.receive_text()


@pytest.mark.asyncio
async def test_ws_fleet_expired_token(client: TestClient, ws_test_setup):
    """Test that expired token rejects connection."""
    cid = ws_test_setup["company1"].id
    token = await ws_test_setup["create_user_token"](ws_test_setup["manager1"], is_expired=True)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/fleet/{cid}?token={token}") as ws:
            ws.receive_text()


@pytest.mark.asyncio
async def test_ws_fleet_revoked_session(client: TestClient, ws_test_setup):
    """Test that revoked session rejects connection."""
    cid = ws_test_setup["company1"].id
    token = await ws_test_setup["create_user_token"](ws_test_setup["manager1"], is_revoked=True)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/fleet/{cid}?token={token}") as ws:
            ws.receive_text()


@pytest.mark.asyncio
async def test_ws_fleet_authorized_manager(client: TestClient, ws_test_setup):
    """Test authorized fleet manager can connect and ping."""
    cid = ws_test_setup["company1"].id
    token = await ws_test_setup["create_user_token"](ws_test_setup["manager1"])
    with client.websocket_connect(f"/api/v1/ws/fleet/{cid}?token={token}") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] == "connection_established"
        ws.send_json({"type": "ping"})
        resp = ws.receive_json()
        assert resp["type"] == "pong"


@pytest.mark.asyncio
async def test_ws_fleet_cross_tenant_rejected(client: TestClient, ws_test_setup):
    """Test manager from Company 2 cannot connect to Company 1's fleet stream."""
    cid1 = ws_test_setup["company1"].id
    token_mgr2 = await ws_test_setup["create_user_token"](ws_test_setup["manager2"])
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/fleet/{cid1}?token={token_mgr2}") as ws:
            ws.receive_text()


@pytest.mark.asyncio
async def test_ws_fleet_driver_role_rejected(client: TestClient, ws_test_setup):
    """Test driver role cannot subscribe to fleet-wide stream."""
    cid = ws_test_setup["company1"].id
    driver_token = await ws_test_setup["create_user_token"](ws_test_setup["driver_user1"])
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/fleet/{cid}?token={driver_token}") as ws:
            ws.receive_text()


@pytest.mark.asyncio
async def test_ws_driver_own_stream_authorized(client: TestClient, ws_test_setup):
    """Test driver can connect to their own driver stream."""
    d1_id = ws_test_setup["driver1"].id
    driver_token = await ws_test_setup["create_user_token"](ws_test_setup["driver_user1"])
    with client.websocket_connect(f"/api/v1/ws/driver/{d1_id}?token={driver_token}") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] == "connection_established"
        assert init_msg["driver_id"] == d1_id


@pytest.mark.asyncio
async def test_ws_driver_other_driver_rejected(client: TestClient, ws_test_setup):
    """Test driver 2 cannot connect to driver 1's stream."""
    d1_id = ws_test_setup["driver1"].id
    driver2_token = await ws_test_setup["create_user_token"](ws_test_setup["driver_user2"])
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/driver/{d1_id}?token={driver2_token}") as ws:
            ws.receive_text()
