import pytest
import pytest_asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from models.user import User, UserRole
from models.company import Company
from models.driver_domain import Driver, DriverStatus
from models.admin_domain import AdminUser, AdminRole, AdminRoleType
from models.support_domain import (
    SupportTicket,
    SupportTicketMessage,
    PasswordResetRequestAdmin,
    TicketStatus,
    TicketPriority,
    TicketCategory,
    RequesterType,
    MessageType,
)
from services.admin_auth_service import create_access_token as create_admin_token
from utils.security import hash_password


@pytest_asyncio.fixture
async def setup_admin(db_session: AsyncSession):
    """Create Super Admin role and user in the test database."""
    role_res = await db_session.execute(
        select(AdminRole).where(AdminRole.name == AdminRoleType.SUPER_ADMIN)
    )
    admin_role = role_res.scalar_one_or_none()
    if not admin_role:
        admin_role = AdminRole(
            name=AdminRoleType.SUPER_ADMIN,
            description="Super Administrator"
        )
        db_session.add(admin_role)
        await db_session.flush()

    uid = uuid.uuid4().hex[:6]
    admin_user = AdminUser(
        full_name=f"Super Admin {uid}",
        email=f"superadmin_{uid}@thevahan.com",
        password_hash=hash_password("SuperSecret123!"),
        role_id=admin_role.id,
        is_active=True,
    )
    db_session.add(admin_user)
    await db_session.flush()
    await db_session.refresh(admin_user)

    token = create_admin_token(
        data={"admin_id": str(admin_user.id), "role": "SUPER_ADMIN"},
        expires_delta=timedelta(hours=2)
    )
    return {"user": admin_user, "token": token}


def _register_owner(client: TestClient):
    uid = uuid.uuid4().hex[:6]
    rand_num = random.randint(10000000, 99999999)
    res = client.post("/api/v1/auth/register", json={
        "company_name": f"Fleet {uid} Logistics",
        "owner_name": f"Owner {uid}",
        "mobile_number": f"98{rand_num}",
        "email": f"owner_{uid}@fleet.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert res.status_code in [200, 201], f"Registration failed: {res.text}"
    data = res.json()
    return {
        "token": data["token"]["access_token"],
        "user": data["user"],
        "company": data["company"],
    }


@pytest_asyncio.fixture
async def setup_driver(db_session: AsyncSession, client: TestClient):
    """Setup a registered driver with an active auth token and driver profile."""
    owner_info = _register_owner(client)
    company_id = owner_info["company"]["id"]

    uid = uuid.uuid4().hex[:6]
    rand_num = random.randint(10000000, 99999999)
    driver_user = User(
        company_id=company_id,
        email=f"driver_{uid}@thevahan.com",
        mobile_number=f"+9188{rand_num}",
        full_name=f"Driver {uid}",
        password_hash=hash_password("Driver123!"),
        role=UserRole.DRIVER,
        is_active=True,
    )
    db_session.add(driver_user)
    await db_session.flush()

    driver_profile = Driver(
        user_id=driver_user.id,
        company_id=company_id,
        name=driver_user.full_name,
        phone_number=driver_user.mobile_number,
        status=DriverStatus.ACTIVE,
    )
    db_session.add(driver_profile)
    await db_session.flush()
    await db_session.refresh(driver_profile)

    from services.auth_service import create_token_for_user
    token_resp = await create_token_for_user(driver_user, db_session)

    return {
        "user": driver_user,
        "driver": driver_profile,
        "token": token_resp.access_token,
        "company_id": company_id,
    }


def test_fleet_owner_ticket_creation_and_message_thread(client: TestClient):
    """Test fleet owner creating a ticket, fetching details, and listing messages."""
    owner = _register_owner(client)
    headers = {"Authorization": f"Bearer {owner['token']}"}

    # 1. Create ticket via /api/v1/support/tickets
    create_payload = {
        "title": "GPS Device Not Tracking",
        "description": "Vehicle MH-12-AB-1234 stopped reporting location 2 hours ago.",
        "category": "TECHNICAL",
        "priority": "HIGH"
    }
    res = client.post("/api/v1/support/tickets", json=create_payload, headers=headers)
    assert res.status_code == 201, res.text
    ticket = res.json()
    assert ticket["ticket_id"].startswith("TICK-")
    assert ticket["status"] == "OPEN"
    assert ticket["category"] == "TECHNICAL"
    assert ticket["priority"] == "HIGH"
    assert ticket["requester_type"] == "FLEET_OWNER"
    assert ticket["company_id"] == owner["company"]["id"]

    ticket_code = ticket["ticket_id"]

    # 2. Get ticket detail
    detail_res = client.get(f"/api/v1/support/tickets/{ticket_code}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == create_payload["title"]

    # 3. List messages on ticket
    msgs_res = client.get(f"/api/v1/support/tickets/{ticket_code}/messages", headers=headers)
    assert msgs_res.status_code == 200
    msgs = msgs_res.json()
    assert len(msgs) >= 1
    assert msgs[0]["content"] == create_payload["description"]
    assert msgs[0]["message_type"] == "PUBLIC"


def test_tenant_isolation_support_tickets(client: TestClient):
    """Ensure strict tenant isolation: Tenant B cannot view or reply to Tenant A's tickets."""
    owner_a = _register_owner(client)
    owner_b = _register_owner(client)

    headers_a = {"Authorization": f"Bearer {owner_a['token']}"}
    headers_b = {"Authorization": f"Bearer {owner_b['token']}"}

    # Owner A creates ticket
    res_a = client.post("/api/v1/support/tickets", json={
        "title": "Confidential Tenant A Issue",
        "description": "Sensitive billing details for Tenant A",
        "category": "PAYMENT"
    }, headers=headers_a)
    assert res_a.status_code == 201
    ticket_a = res_a.json()
    ticket_a_code = ticket_a["ticket_id"]

    # Owner B attempts to view ticket A detail -> 404
    hack_res = client.get(f"/api/v1/support/tickets/{ticket_a_code}", headers=headers_b)
    assert hack_res.status_code == 404

    # Owner B attempts to view ticket A messages -> 404
    hack_msg_res = client.get(f"/api/v1/support/tickets/{ticket_a_code}/messages", headers=headers_b)
    assert hack_msg_res.status_code == 404

    # Owner B attempts to post reply to ticket A -> 404
    hack_post_res = client.post(
        f"/api/v1/support/tickets/{ticket_a_code}/messages",
        json={"content": "Malicious intrusion attempt"},
        headers=headers_b
    )
    assert hack_post_res.status_code == 404

    # Owner B lists tickets -> ticket A is NOT present
    list_b = client.get("/api/v1/support/tickets", headers=headers_b)
    assert list_b.status_code == 200
    ticket_ids_b = [t["ticket_id"] for t in list_b.json()]
    assert ticket_a_code not in ticket_ids_b


@pytest.mark.asyncio
async def test_super_admin_full_support_workflow(client: TestClient, setup_admin):
    """
    Super Admin end-to-end workflow:
    - View all tickets across tenants (including no-trailing-slash path)
    - Add private internal notes (hidden from user)
    - Add public reply (visible to user)
    - Status transitions and closing tickets
    """
    admin_token = setup_admin["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    owner = _register_owner(client)
    owner_headers = {"Authorization": f"Bearer {owner['token']}"}

    # 1. Owner creates a ticket
    create_res = client.post("/api/v1/support/tickets", json={
        "title": "Engine light blinking on truck 05",
        "description": "Truck 05 is showing diagnostic code P0300.",
        "category": "TECHNICAL",
        "priority": "HIGH"
    }, headers=owner_headers)
    assert create_res.status_code == 201
    ticket = create_res.json()
    ticket_id = ticket["id"]
    ticket_code = ticket["ticket_id"]

    # 2. Super Admin views all tickets at /api/v1/admin/tickets (no trailing slash)
    admin_list_res = client.get("/api/v1/admin/tickets", headers=admin_headers)
    assert admin_list_res.status_code == 200
    all_tickets = admin_list_res.json()
    found = any(t["ticket_id"] == ticket_code for t in all_tickets)
    assert found, "Created ticket was not found in Super Admin inbox"

    # Also test slash endpoint
    admin_list_slash = client.get("/api/v1/admin/tickets/", headers=admin_headers)
    assert admin_list_slash.status_code == 200

    # 3. Super Admin posts an INTERNAL NOTE
    internal_res = client.post(
        f"/api/v1/admin/tickets/{ticket_id}/messages",
        json={
            "content": "Assigned technician Dave to inspect spark plug harness on truck 05.",
            "message_type": "INTERNAL_NOTE"
        },
        headers=admin_headers
    )
    assert internal_res.status_code == 200
    assert internal_res.json()["message_type"] == "INTERNAL_NOTE"

    # 4. Super Admin posts a PUBLIC reply
    public_res = client.post(
        f"/api/v1/admin/tickets/{ticket_id}/messages",
        json={
            "content": "Hello! We have dispatched our mobile service van to check your truck.",
            "message_type": "PUBLIC"
        },
        headers=admin_headers
    )
    assert public_res.status_code == 200
    assert public_res.json()["message_type"] == "PUBLIC"

    # 5. Customer checks ticket messages:
    # MUST see the public reply, but MUST NOT see the internal note!
    owner_msgs_res = client.get(f"/api/v1/support/tickets/{ticket_code}/messages", headers=owner_headers)
    assert owner_msgs_res.status_code == 200
    owner_msgs = owner_msgs_res.json()

    contents = [m["content"] for m in owner_msgs]
    assert any("mobile service van" in c for c in contents), "Public reply not visible to customer"
    assert not any("spark plug harness" in c for c in contents), "CRITICAL: Internal note leaked to customer!"

    # 6. Customer replies to the ticket
    customer_reply_res = client.post(
        f"/api/v1/support/tickets/{ticket_code}/messages",
        json={"content": "Thank you, driver is waiting at Toll Plaza 4."},
        headers=owner_headers
    )
    assert customer_reply_res.status_code == 201

    # 7. Super Admin checks all messages: sees BOTH public and internal note
    admin_msgs_res = client.get(f"/api/v1/admin/tickets/{ticket_id}/messages", headers=admin_headers)
    assert admin_msgs_res.status_code == 200
    admin_msg_contents = [m["content"] for m in admin_msgs_res.json()]
    assert any("spark plug harness" in c for c in admin_msg_contents)
    assert any("Toll Plaza 4" in c for c in admin_msg_contents)

    # 8. Super Admin updates status to RESOLVED
    resolve_res = client.patch(
        f"/api/v1/admin/tickets/{ticket_id}/status",
        json={"status": "RESOLVED", "internal_note": "Service van replaced ignition coil."},
        headers=admin_headers
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"
    assert resolve_res.json()["resolved_at"] is not None

    # 9. Super Admin closes ticket
    close_res = client.patch(
        f"/api/v1/admin/tickets/{ticket_id}/status",
        json={"status": "CLOSED"},
        headers=admin_headers
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"

    # 10. Customer tries to post to closed ticket -> rejected with 400
    rejected_res = client.post(
        f"/api/v1/support/tickets/{ticket_code}/messages",
        json={"content": "Can you check one more thing?"},
        headers=owner_headers
    )
    assert rejected_res.status_code == 400
    assert "closed" in rejected_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_driver_sos_and_assistance_in_super_admin(client: TestClient, setup_driver, setup_admin):
    """
    Verify Driver SOS emergency alert & Driver assistance requests:
    - Driver triggers SOS -> Creates EmergencyAlert and SupportTicket
    - Super Admin sees emergency ticket with URGENT priority in admin portal
    - Driver submits non-emergency assistance -> appears in Super Admin inbox
    """
    driver_token = setup_driver["token"]
    driver_headers = {"Authorization": f"Bearer {driver_token}"}
    admin_headers = {"Authorization": f"Bearer {setup_admin['token']}"}

    # 1. Driver triggers SOS
    sos_res = client.post(
        "/api/v1/driver-app/sos",
        json={
            "latitude": 18.5204,
            "longitude": 73.8567,
            "message": "Brake failure on highway near Pune bypass!"
        },
        headers=driver_headers
    )
    assert sos_res.status_code == 201, sos_res.text
    sos_data = sos_res.json()
    assert sos_data["ticket_id"] is not None
    assert sos_data["ticket_id"].startswith("SOS-")

    # 2. Super Admin queries tickets filtered by requester_type=DRIVER
    admin_res = client.get("/api/v1/admin/tickets?requester_type=DRIVER", headers=admin_headers)
    assert admin_res.status_code == 200
    driver_tickets = admin_res.json()
    assert len(driver_tickets) >= 1

    sos_ticket = next((t for t in driver_tickets if t["ticket_id"] == sos_data["ticket_id"]), None)
    assert sos_ticket is not None
    assert sos_ticket["priority"] == "URGENT"
    assert "Brake failure" in sos_ticket["description"]
    assert sos_ticket["requester_name"] == setup_driver["driver"].name

    # 3. Driver submits technical assistance request
    assist_res = client.post(
        "/api/v1/driver-app/assistance",
        json={
            "title": "Fastag not scanning at toll plaza",
            "description": "RFID tag error at Khed Shivapur toll.",
            "category": "TECHNICAL",
            "priority": "HIGH"
        },
        headers=driver_headers
    )
    assert assist_res.status_code == 201
    assist_ticket = assist_res.json()
    assert assist_ticket["ticket_id"].startswith("DRV-")

    # 4. Super Admin searches for Fastag ticket
    search_res = client.get("/api/v1/admin/tickets?search=Fastag", headers=admin_headers)
    assert search_res.status_code == 200
    matching = search_res.json()
    assert len(matching) >= 1
    assert any(t["ticket_id"] == assist_ticket["ticket_id"] for t in matching)


@pytest.mark.asyncio
async def test_password_reset_super_admin_workflow(client: TestClient, setup_admin):
    """
    Test Password Reset Request workflow:
    - User initiates forgot password
    - Appears in Super Admin Password Resets inbox
    - Super Admin approves/rejects
    """
    admin_headers = {"Authorization": f"Bearer {setup_admin['token']}"}

    owner = _register_owner(client)
    owner_email = owner["user"]["email"]

    # 1. User requests password reset
    forgot_res = client.post(
        "/api/v1/auth/forgot-password/request",
        json={"identifier": owner_email}
    )
    assert forgot_res.status_code == 200

    # 2. Super Admin lists password reset requests (no-trailing-slash and trailing-slash)
    resets_res = client.get("/api/v1/admin/password-resets", headers=admin_headers)
    assert resets_res.status_code == 200
    resets = resets_res.json()
    assert len(resets) >= 1

    target_req = next((r for r in resets if r["requester_email_phone"] == owner_email), None)
    assert target_req is not None
    assert target_req["status"] == "PENDING"
    req_id = target_req["id"]

    # 3. Super Admin approves the request
    approve_res = client.post(f"/api/v1/admin/password-resets/{req_id}/approve", headers=admin_headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"

    # 4. Super Admin lists filtered by status=APPROVED
    approved_list = client.get("/api/v1/admin/password-resets?status=APPROVED", headers=admin_headers)
    assert approved_list.status_code == 200
    assert any(r["id"] == req_id for r in approved_list.json())


@pytest.mark.asyncio
async def test_admin_dashboard_metrics(client: TestClient, setup_admin):
    """
    Test Super Admin operations dashboard metrics and recent activity feeds.
    """
    admin_headers = {"Authorization": f"Bearer {setup_admin['token']}"}

    # 1. Fetch dashboard metrics
    metrics_res = client.get("/api/v1/admin/dashboard/metrics", headers=admin_headers)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert "open_tickets" in metrics
    assert "pending_verifications" in metrics
    assert "resolved_today" in metrics
    assert "active_agents" in metrics
    assert "pending_password_resets" in metrics

    # 2. Fetch recent activity audit log
    activity_res = client.get("/api/v1/admin/dashboard/recent-activity", headers=admin_headers)
    assert activity_res.status_code == 200
    activities = activity_res.json()
    assert isinstance(activities, list)
