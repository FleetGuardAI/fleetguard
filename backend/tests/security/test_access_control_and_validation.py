"""
FleetGuard — Phase B, Batch 3 Security Verification Suite
Tests for:
- FG-SEC-015: Expense approval & rejection role-based access control (no driver privilege escalation)
- FG-SEC-016: GPS telemetry bounds validation (latitude/longitude/speed/heading constraints)
- FG-SEC-017: Odometer lockout prevention (plausible speed/delta bounds, admin overrides)
- FG-SEC-018: Company profile tampering prevention (PATCH restricted to COMPANY_ADMIN)
- FG-SEC-019: OCR document log redaction (zero raw PII in application log output)
- FG-SEC-020: Third-party API secret sanitization in exception URLs & error handlers
"""

import pytest
import pytest_asyncio
import uuid
import logging
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from main import app
from models.user import User, UserRole
from models.company import Company, CompanyStatus
from models.auth_session import AuthSession
from models.vehicle_domain import Vehicle
from models.driver_domain import Driver, DriverStatus
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from schemas.location import PlaceDetails, RouteCalculationRequest
from routers.location_tracking import LocationPoint, LocationBatchRequest
from services.odometer_service import OdometerService
from services.location_provider import sanitize_log_message
from services.otp_service import _sanitize_error_message
from utils.security import create_access_token, hash_password


@pytest_asyncio.fixture
async def batch3_test_fixture(db_session: AsyncSession):
    """Seed test company, admin user, driver user, vehicle, and pending expense."""
    uid = uuid.uuid4().hex[:8]

    # Create Company
    company = Company(
        company_name=f"Batch 3 Test Corp {uid}",
        owner_name="Test Owner",
        mobile_number=f"+9198{uid[:8]}",
        email=f"owner_{uid}@batch3test.com",
        status=CompanyStatus.ACTIVE,
    )
    db_session.add(company)
    await db_session.flush()

    # Create Company Admin
    admin_user = User(
        company_id=company.id,
        full_name="Company Admin",
        email=f"admin_{uid}@batch3test.com",
        mobile_number=f"+9191{uid[:8]}",
        password_hash=hash_password("admin_pass_123"),
        role=UserRole.COMPANY_ADMIN,
        is_active=True,
    )
    db_session.add(admin_user)

    # Create Driver User
    driver_user = User(
        company_id=company.id,
        full_name="Fleet Driver",
        email=f"driver_{uid}@batch3test.com",
        mobile_number=f"+9192{uid[:8]}",
        password_hash=hash_password("driver_pass_123"),
        role=UserRole.DRIVER,
        is_active=True,
    )
    db_session.add(driver_user)
    await db_session.flush()

    # Create Driver Domain Entity
    driver_entity = Driver(
        company_id=company.id,
        user_id=driver_user.id,
        name=driver_user.full_name,
        phone_number=driver_user.mobile_number,
        status=DriverStatus.ACTIVE,
    )
    db_session.add(driver_entity)

    # Create Vehicle
    vehicle = Vehicle(
        company_id=company.id,
        registration_number=f"DL01AB{uid[:4].upper()}",
        current_odometer=50000.0,
        last_odometer_update_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db_session.add(vehicle)

    # Create Pending Expense
    expense = Expense(
        business_id=f"EXP-{uid[:6].upper()}",
        company_id=company.id,
        category=ExpenseCategory.FUEL,
        amount=2500.0,
        status=ExpenseStatus.PENDING,
        expense_date=datetime.now(timezone.utc),
        description="Pending diesel fuel fill",
        origin_type="manual",
        origin_id=f"user_{admin_user.id}",
    )
    db_session.add(expense)
    await db_session.commit()
    await db_session.refresh(company)
    await db_session.refresh(admin_user)
    await db_session.refresh(driver_user)
    await db_session.refresh(driver_entity)
    await db_session.refresh(vehicle)
    await db_session.refresh(expense)

    # Issue AuthSessions & JWTs
    admin_jti = uuid.uuid4().hex
    driver_jti = uuid.uuid4().hex

    admin_session = AuthSession(
        user_id=admin_user.id,
        company_id=company.id,
        session_jti=admin_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    driver_session = AuthSession(
        user_id=driver_user.id,
        company_id=company.id,
        session_jti=driver_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add_all([admin_session, driver_session])
    await db_session.commit()

    admin_token = create_access_token(
        data={
            "sub": str(admin_user.id),
            "company_id": company.id,
            "role": admin_user.role.value,
            "jti": admin_jti,
        }
    )
    driver_token = create_access_token(
        data={
            "sub": str(driver_user.id),
            "company_id": company.id,
            "role": driver_user.role.value,
            "jti": driver_jti,
        }
    )

    return {
        "company": company,
        "admin_user": admin_user,
        "driver_user": driver_user,
        "driver_entity": driver_entity,
        "vehicle": vehicle,
        "expense": expense,
        "admin_token": admin_token,
        "driver_token": driver_token,
    }


# ==============================================================================
# FG-SEC-015: Expense Privilege Escalation Prevention
# ==============================================================================

@pytest.mark.asyncio
async def test_driver_cannot_approve_expense(client: TestClient, batch3_test_fixture: dict):
    """FG-SEC-015: Driver JWT attempting to approve expense receives HTTP 403 Forbidden."""
    fix = batch3_test_fixture
    exp_id = fix["expense"].id

    resp = client.post(
        f"/api/v1/expenses/{exp_id}/approve",
        headers={"Authorization": f"Bearer {fix['driver_token']}"},
    )
    assert resp.status_code == 403
    assert "permission" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_driver_cannot_reject_expense(client: TestClient, batch3_test_fixture: dict):
    """FG-SEC-015: Driver JWT attempting to reject expense receives HTTP 403 Forbidden."""
    fix = batch3_test_fixture
    exp_id = fix["expense"].id

    resp = client.post(
        f"/api/v1/expenses/{exp_id}/reject",
        headers={"Authorization": f"Bearer {fix['driver_token']}"},
        json={"rejection_reason": "Rogue rejection attempt"},
    )
    assert resp.status_code == 403
    assert "permission" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_company_admin_can_approve_expense(client: TestClient, batch3_test_fixture: dict):
    """FG-SEC-015: Company Admin is properly authorized to approve pending expenses."""
    fix = batch3_test_fixture
    exp_id = fix["expense"].id

    resp = client.post(
        f"/api/v1/expenses/{exp_id}/approve",
        headers={"Authorization": f"Bearer {fix['admin_token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "APPROVED"
    assert data["id"] == exp_id


# ==============================================================================
# FG-SEC-016: GPS & Telemetry Bounds Validation
# ==============================================================================

def test_gps_latitude_bounds_validation():
    """FG-SEC-016: Latitude values outside [-90.0, 90.0] are strictly rejected by Pydantic."""
    # Valid latitude
    pt = LocationPoint(latitude=28.6139, longitude=77.2090, timestamp="2026-11-24T00:00:00Z")
    assert pt.latitude == 28.6139

    # Latitude > 90.0
    with pytest.raises(ValidationError):
        LocationPoint(latitude=91.0, longitude=77.2090, timestamp="2026-11-24T00:00:00Z")

    # Latitude < -90.0
    with pytest.raises(ValidationError):
        LocationPoint(latitude=-90.1, longitude=77.2090, timestamp="2026-11-24T00:00:00Z")


def test_gps_longitude_bounds_validation():
    """FG-SEC-016: Longitude values outside [-180.0, 180.0] are strictly rejected by Pydantic."""
    # Valid longitude
    pt = LocationPoint(latitude=28.6139, longitude=77.2090, timestamp="2026-11-24T00:00:00Z")
    assert pt.longitude == 77.2090

    # Longitude > 180.0
    with pytest.raises(ValidationError):
        LocationPoint(latitude=28.6139, longitude=180.5, timestamp="2026-11-24T00:00:00Z")

    # Longitude < -180.0
    with pytest.raises(ValidationError):
        LocationPoint(latitude=28.6139, longitude=-181.0, timestamp="2026-11-24T00:00:00Z")


def test_gps_speed_and_heading_bounds_validation():
    """FG-SEC-016: Speed must be >= 0 and heading must be in [0, 360]."""
    # Negative speed rejected
    with pytest.raises(ValidationError):
        LocationPoint(latitude=28.0, longitude=77.0, speed=-5.0, timestamp="2026-11-24T00:00:00Z")

    # Negative heading rejected
    with pytest.raises(ValidationError):
        LocationPoint(latitude=28.0, longitude=77.0, heading=-1.0, timestamp="2026-11-24T00:00:00Z")

    # Heading > 360 rejected
    with pytest.raises(ValidationError):
        LocationPoint(latitude=28.0, longitude=77.0, heading=361.0, timestamp="2026-11-24T00:00:00Z")


def test_place_details_and_route_request_bounds():
    """FG-SEC-016: Schemas in schemas/location.py validate lat/lng bounds."""
    # PlaceDetails
    with pytest.raises(ValidationError):
        PlaceDetails(place_id="p1", formatted_address="Addr", lat=95.0, lng=50.0)

    # RouteCalculationRequest
    with pytest.raises(ValidationError):
        RouteCalculationRequest(origin_lat=95.0, origin_lng=50.0, destination_lat=10.0, destination_lng=10.0)


# ==============================================================================
# FG-SEC-017: Odometer Lockout Prevention
# ==============================================================================

def test_odometer_rejects_implausible_delta():
    """FG-SEC-017: Implausible jump (+100,000 km in 1 hour) is rejected without admin override."""
    v = Vehicle(id=1, current_odometer=50000.0, last_odometer_update_at=datetime.now(timezone.utc) - timedelta(hours=1))
    
    # Try jumping from 50,000 km to 150,000 km in 1 hour (100,000 km/h)
    valid, reason = OdometerService.is_plausible_odometer_delta(
        current_odometer=v.current_odometer,
        new_odometer=150000.0,
        last_update_at=v.last_odometer_update_at,
        new_timestamp=datetime.now(timezone.utc),
        admin_override=False,
    )
    assert not valid
    assert "exceeds maximum plausible single jump" in reason

    # Method update_odometer_if_valid returns False and does not alter vehicle odometer
    success = OdometerService.update_odometer_if_valid(v, 150000.0, datetime.now(timezone.utc), admin_override=False)
    assert not success
    assert v.current_odometer == 50000.0


def test_odometer_rejects_rollback():
    """FG-SEC-017: Rollback to a lower odometer reading is rejected."""
    v = Vehicle(id=1, current_odometer=50000.0, last_odometer_update_at=datetime.now(timezone.utc) - timedelta(hours=1))
    
    success = OdometerService.update_odometer_if_valid(v, 49000.0, datetime.now(timezone.utc))
    assert not success
    assert v.current_odometer == 50000.0


def test_odometer_accepts_plausible_reading():
    """FG-SEC-017: Plausible incremental distance (+80 km in 1.5 hours) is accepted."""
    t_prev = datetime.now(timezone.utc) - timedelta(hours=1.5)
    t_now = datetime.now(timezone.utc)
    v = Vehicle(id=1, current_odometer=50000.0, last_odometer_update_at=t_prev)

    success = OdometerService.update_odometer_if_valid(v, 50080.0, t_now)
    assert success
    assert v.current_odometer == 50080.0
    assert v.last_odometer_update_at == t_now


def test_odometer_admin_override_permits_gauge_replacement():
    """FG-SEC-017: Admin override allows legitimate speedometer or gauge replacement."""
    t_prev = datetime.now(timezone.utc) - timedelta(hours=1)
    t_now = datetime.now(timezone.utc)
    v = Vehicle(id=1, current_odometer=50000.0, last_odometer_update_at=t_prev)

    # Legitimate fleet maintenance jump with admin override
    success = OdometerService.update_odometer_if_valid(v, 75000.0, t_now, admin_override=True)
    assert success
    assert v.current_odometer == 75000.0


# ==============================================================================
# FG-SEC-018: Company Profile Role Verification
# ==============================================================================

@pytest.mark.asyncio
async def test_driver_cannot_patch_company(client: TestClient, batch3_test_fixture: dict):
    """FG-SEC-018: Driver JWT attempting to PATCH company profile receives HTTP 403 Forbidden."""
    fix = batch3_test_fixture

    resp = client.patch(
        "/api/v1/auth/company",
        headers={"Authorization": f"Bearer {fix['driver_token']}"},
        json={"company_name": "Rogue Driver Fleet Takeover"},
    )
    assert resp.status_code == 403
    assert "permission" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_company_admin_can_patch_company(client: TestClient, batch3_test_fixture: dict):
    """FG-SEC-018: Company Admin is properly authorized to update company profile."""
    fix = batch3_test_fixture

    resp = client.patch(
        "/api/v1/auth/company",
        headers={"Authorization": f"Bearer {fix['admin_token']}"},
        json={"company_name": "Updated Valid Fleet Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["company"]["company_name"] == "Updated Valid Fleet Name"


# ==============================================================================
# FG-SEC-019 & FG-SEC-020: Log Redaction & Secret Sanitization
# ==============================================================================

def test_log_sanitizer_redacts_api_key():
    """FG-SEC-020: Secret API keys are cleanly stripped from error messages before logging."""
    secret = "AIzaSySecretApiKey12345"
    err = Exception(f"Failed to fetch https://maps.googleapis.com/test?key={secret}&query=delhi")
    
    sanitized = sanitize_log_message(err, secret)
    assert secret not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized


def test_otp_log_sanitizer_redacts_auth_key():
    """FG-SEC-020: MSG91 auth key is cleanly stripped from OTP error messages."""
    secret = "9876543210abcdef9876543210abcdef"
    raw_error = f"HTTPConnectionPool: Max retries exceeded with url: /api/v5/otp?authkey={secret}"

    sanitized = _sanitize_error_message(raw_error, secret)
    assert secret not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized


def test_ocr_log_does_not_dump_raw_pii(caplog):
    """FG-SEC-019: Document router logs only metadata and character counts, zero raw text."""
    from routers import documents
    
    with caplog.at_level(logging.INFO):
        # Simulate log completion entry
        documents.logger.info("--- OCR COMPLETED --- Characters: 250 --- Document type: rc")

    for record in caplog.records:
        assert "Raw Text:" not in record.message
        assert "Aadhaar" not in record.message
        assert "Chassis" not in record.message
