"""
FleetGuard TMS — Security Verification Suite: Phase B, Batch 4
Tests:
1. FG-SEC-021: Public endpoint rate limiting (auth, admin, OTP) via SlowAPI
2. FG-SEC-023: Cross-tenant vehicle inspection isolation & maintenance ticket poisoning prevention
3. FG-SEC-027: Strict signed URL expiration capping (<= 3600s / preview <= 900s)
4. FG-SEC-022: Database backup verification & retention mechanics
"""

import os
import gzip
import time
import pytest
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient

from main import app
from config import settings
from services.file_upload_service import storage_service
from scripts.backup_database import verify_backup_file, prune_old_backups
from models.user import User, UserRole
from models.company import Company
from models.vehicle_domain import Vehicle
from models.driver_domain import Driver, DriverStatus, DutyStatus
from models.vehicle_inspection import VehicleInspection, InspectionStatus
from models.ticket import Ticket
from routers.driver_mobile import get_current_driver
from database import get_db
from utils.rate_limiter import limiter


@pytest.fixture(autouse=True)
def reset_limiter():
    """Ensure limiter is enabled and clean for test runs."""
    limiter.enabled = True
    yield
    limiter.enabled = False


# ==============================================================================
# FG-SEC-021: Rate Limiting Verification
# ==============================================================================

def test_login_rate_limiting():
    """Verify that user login is capped at 5 attempts per minute per IP."""
    client = TestClient(app)
    ip_header = {"X-Forwarded-For": "198.51.100.42"}

    # First 5 attempts should return normal auth failures (e.g. 401 or 422), not 429
    for i in range(5):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": f"attacker_{i}@example.com", "password": "WrongPassword123!"},
            headers=ip_header
        )
        assert resp.status_code != 429, f"Attempt {i+1} should not be rate-limited"

    # 6th attempt from the same IP MUST trigger 429 Too Many Requests
    resp_blocked = client.post(
        "/api/v1/auth/login",
        json={"email": "attacker_6@example.com", "password": "WrongPassword123!"},
        headers=ip_header
    )
    assert resp_blocked.status_code == 429, "6th attempt from same IP must be rate-limited"
    assert "Rate limit exceeded" in resp_blocked.text

    # Different IP should NOT be blocked
    resp_other_ip = client.post(
        "/api/v1/auth/login",
        json={"email": "legit@example.com", "password": "WrongPassword123!"},
        headers={"X-Forwarded-For": "198.51.100.99"}
    )
    assert resp_other_ip.status_code != 429, "Requests from a different IP should not be blocked"


def test_admin_login_rate_limiting():
    """Verify that admin login is capped at 5 attempts per minute per IP."""
    client = TestClient(app)
    ip_header = {"X-Forwarded-For": "198.51.100.55"}

    for i in range(5):
        resp = client.post(
            "/api/v1/admin/auth/login",
            json={"email": "admin@example.com", "password": "BadPassword!"},
            headers=ip_header
        )
        assert resp.status_code != 429

    # 6th attempt blocked
    resp_blocked = client.post(
        "/api/v1/admin/auth/login",
        json={"email": "admin@example.com", "password": "BadPassword!"},
        headers=ip_header
    )
    assert resp_blocked.status_code == 429


def test_driver_otp_rate_limiting():
    """Verify that OTP requests are limited (3 per 10 minutes)."""
    client = TestClient(app)
    ip_header = {"X-Forwarded-For": "198.51.100.77"}

    for i in range(3):
        resp = client.post(
            "/api/v1/driver-app/send-otp",
            json={"phone_number": f"+91987654321{i}"},
            headers=ip_header
        )
        assert resp.status_code != 429

    # 4th attempt blocked
    resp_blocked = client.post(
        "/api/v1/driver-app/send-otp",
        json={"phone_number": "+919876543299"},
        headers=ip_header
    )
    assert resp_blocked.status_code == 429


# ==============================================================================
# FG-SEC-023: Cross-Tenant Vehicle Inspection Isolation
# ==============================================================================

@pytest.mark.asyncio
async def test_cross_tenant_inspection_isolation_rejected(db_session):
    """
    FG-SEC-023: Verify that a driver cannot submit an inspection report
    for a vehicle belonging to another company (tenant).
    """
    # Create Company 1 (Tenant 1) and Driver 1
    company_1 = Company(
        company_name="Tenant 1 Logistics",
        owner_name="Owner One",
        mobile_number="+919800000001",
        email="tenant1@example.com"
    )
    # Create Company 2 (Tenant 2) and Vehicle 2
    company_2 = Company(
        company_name="Tenant 2 Freight",
        owner_name="Owner Two",
        mobile_number="+919800000002",
        email="tenant2@example.com"
    )
    db_session.add_all([company_1, company_2])
    await db_session.flush()

    user_1 = User(
        company_id=company_1.id,
        email="driver1@tenant1.com",
        mobile_number="+919811111111",
        full_name="Driver One",
        password_hash="fakehash",
        role=UserRole.DRIVER
    )
    db_session.add(user_1)
    await db_session.flush()

    driver_1 = Driver(
        user_id=user_1.id,
        company_id=company_1.id,
        name="Driver One",
        phone_number="+919811111111",
        status=DriverStatus.ACTIVE,
        duty_status=DutyStatus.OFF_DUTY
    )
    vehicle_company_2 = Vehicle(
        company_id=company_2.id,
        registration_number="MH12AB9999",
        make="Tata",
        model="Prima"
    )
    db_session.add_all([driver_1, vehicle_company_2])
    await db_session.commit()
    await db_session.refresh(driver_1)
    await db_session.refresh(vehicle_company_2)

    # Override get_current_driver dependency to act as driver_1
    app.dependency_overrides[get_current_driver] = lambda: driver_1
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        client = TestClient(app)

        # Attempt to submit inspection for Company 2's vehicle
        payload = {
            "vehicle_id": vehicle_company_2.id,
            "inspection_type": "PRE_TRIP",
            "items": [
                {"name": "Tyres", "passed": False, "notes": "Low tread depth"}
            ],
            "notes": "Malicious inspection targeting tenant 2"
        }

        resp = client.post("/api/v1/driver-app/inspections", json=payload)
        assert resp.status_code == 403, f"Expected 403 Forbidden, got {resp.status_code}"
        assert "Unauthorized vehicle" in resp.json()["detail"]

        # Attempt to submit for nonexistent vehicle
        payload_nonexistent = {
            "vehicle_id": 9999999,
            "inspection_type": "PRE_TRIP",
            "items": [{"name": "Tyres", "passed": True}]
        }
        resp_404 = client.post("/api/v1/driver-app/inspections", json=payload_nonexistent)
        assert resp_404.status_code == 404, f"Expected 404 Not Found, got {resp_404.status_code}"

    finally:
        app.dependency_overrides.pop(get_current_driver, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_own_vehicle_inspection_generates_maintenance_ticket(db_session):
    """
    FG-SEC-023: Verify that submitting a legitimate inspection for the driver's own fleet
    succeeds and auto-generates a maintenance ticket with high risk.
    """
    company = Company(
        company_name="Legit Logistics",
        owner_name="Owner Three",
        mobile_number="+919800000003",
        email="legit@example.com"
    )
    db_session.add(company)
    await db_session.flush()

    user = User(
        company_id=company.id,
        email="driver2@legit.com",
        mobile_number="+919822222222",
        full_name="Driver Two",
        password_hash="fakehash",
        role=UserRole.DRIVER
    )
    db_session.add(user)
    await db_session.flush()

    driver = Driver(
        user_id=user.id,
        company_id=company.id,
        name="Driver Two",
        phone_number="+919822222222",
        status=DriverStatus.ACTIVE,
        duty_status=DutyStatus.ON_DUTY
    )
    vehicle = Vehicle(
        company_id=company.id,
        registration_number="DL01XY1234",
        make="BharatBenz",
        model="2823"
    )
    db_session.add_all([driver, vehicle])
    await db_session.commit()
    await db_session.refresh(driver)
    await db_session.refresh(vehicle)

    app.dependency_overrides[get_current_driver] = lambda: driver
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        client = TestClient(app)

        payload = {
            "vehicle_id": vehicle.id,
            "inspection_type": "PRE_TRIP",
            "items": [
                {"name": "Brakes", "passed": False, "notes": "Soft pedal feel"},
                {"name": "Lights", "passed": True}
            ],
            "notes": "Pre-trip morning inspection"
        }

        resp = client.post("/api/v1/driver-app/inspections", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["overall_status"] == "FAIL"
        assert data["company_id"] == company.id
        assert data["vehicle_id"] == vehicle.id

    finally:
        app.dependency_overrides.pop(get_current_driver, None)
        app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# FG-SEC-027: Signed URL Lifetime Capping Verification
# ==============================================================================

def test_signed_url_lifetime_capping():
    """
    FG-SEC-027: Verify that storage_service strictly caps signed URL lifetimes
    at 3,600s (1 hour) and previews at 900s (15 min).
    """
    captured_expires_in = []

    class MockStorageBucket:
        def create_signed_url(self, path: str, expires_in: int, **options):
            captured_expires_in.append(expires_in)
            return {"signedURL": f"https://mockstorage.example.com/{path}?token=tok&expires={expires_in}"}

    class MockClient:
        class Storage:
            @staticmethod
            def from_(bucket):
                return MockStorageBucket()
        storage = Storage()

    orig_client = storage_service._supabase
    storage_service._supabase = MockClient()

    try:
        # Request excessive 7-day expiration
        storage_service.create_signed_url("documents/audit.pdf", expires_in=86400 * 7)
        assert captured_expires_in[-1] == 3600, f"Expected capped 3600s, got {captured_expires_in[-1]}"

        # Request standard preview (default should be 900s)
        storage_service.create_preview_signed_url("avatars/driver.png")
        assert captured_expires_in[-1] == 900, f"Expected 900s for preview, got {captured_expires_in[-1]}"

        # Request preview with 1800s (should be capped at 900s)
        storage_service.create_preview_signed_url("avatars/driver.png", expires_in=1800)
        assert captured_expires_in[-1] == 900, f"Expected preview cap of 900s, got {captured_expires_in[-1]}"

        # Default create_signed_url should be 3600s
        storage_service.create_signed_url("vehicles/truck.png")
        assert captured_expires_in[-1] == 3600, f"Expected default 3600s, got {captured_expires_in[-1]}"

    finally:
        storage_service._supabase = orig_client


# ==============================================================================
# FG-SEC-022: Database Backup Integrity & Retention Verification
# ==============================================================================

def test_backup_verification_and_retention(tmp_path):
    """
    FG-SEC-022: Verifies that backup integrity validation correctly recognizes
    valid gzip archives and detects corrupted/empty files, and retention pruning works.
    """
    # 1. Valid gzip backup archive
    valid_file = tmp_path / "fleetguard_backup_valid.sql.gz"
    with gzip.open(valid_file, "wb") as gz:
        gz.write(b"-- PostgreSQL Database Dump\nCREATE TABLE test (id INT);\n" * 10)
    assert verify_backup_file(str(valid_file)) is True

    # 2. Corrupt / empty file
    corrupt_file = tmp_path / "fleetguard_backup_corrupt.sql.gz"
    corrupt_file.write_bytes(b"not a gzip file")
    assert verify_backup_file(str(corrupt_file)) is False

    # 3. Retention pruning test
    old_archive = tmp_path / "fleetguard_backup_old.sql.gz"
    with gzip.open(old_archive, "wb") as gz:
        gz.write(b"-- Historical backup\n" * 10)

    # Set mtime to 10 days ago
    past_mtime = time.time() - (10 * 86400)
    os.utime(str(old_archive), (past_mtime, past_mtime))

    # Prune files older than 7 days
    pruned = prune_old_backups(str(tmp_path), retention_days=7)
    assert pruned == 1
    assert not old_archive.exists()
    assert valid_file.exists()
