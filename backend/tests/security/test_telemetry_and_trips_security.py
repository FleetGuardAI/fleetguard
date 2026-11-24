"""
FleetGuard — Phase B, Batch 7 Security Verification Suite
Tests:
1. FG-SEC-032: Timing-Safe Verification of Hardware Telematics Webhook Secret
2. FG-SEC-033: Cross-Tenant Telemetry DoS via Duplicate Hardware IMEI Collision Prevention
3. FG-SEC-034: Telemetry Replay & Future/Stale Timestamp Poisoning Bounding
4. FG-SEC-035: Trip Distance Telemetry Frozen Against Retroactive Backdated GPS Points
5. FG-SEC-052: Trip State Machine Bypass Prevention via PATCH /trips/{id} & Terminal State Locking
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from config import settings
from models.user import User, UserRole
from models.company import Company
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus
from models.asset_domain import Asset, AssetInstallationStatus, AssetOperationalStatus, AssetType
from models.trip_domain import Trip, TripStatus
from models.location_tracking import DriverLocation
from models.fuel_log import FuelLog
from schemas.telematics import NormalizedHardwareEvent
from schemas.asset_domain import HardwareAssetCreate
from schemas.trip_domain import TripUpdated
from services.location_service import LocationService
from services.trip_completion_service import TripCompletionService
from services.auth_service import get_current_user
from routers.telematics import verify_telematics_secret
from routers.asset_domain import add_hardware_device
from routers.trip_domain import update_trip
from routers.location_tracking import batch_upload_locations, LocationBatchRequest, LocationPoint


# ==============================================================================
# Helper Fixtures & Objects
# ==============================================================================

class DummyRequest:
    """Mock Starlette Request with app.state.settings."""
    def __init__(self, settings_obj):
        class State:
            pass
        self.state = State()
        self.app = State()
        self.app.state = State()
        self.app.state.settings = settings_obj


# ==============================================================================
# 1. FG-SEC-032: Timing-Safe Telematics Webhook Verification
# ==============================================================================

def test_telematics_secret_verification_valid():
    """Verify that a valid telematics secret passes verification."""
    req = DummyRequest(settings)
    secret = settings.TELEMATICS_WEBHOOK_SECRET or "valid_secret_123"
    settings.TELEMATICS_WEBHOOK_SECRET = secret

    assert verify_telematics_secret(req, api_key_header=secret) is True


def test_telematics_secret_verification_invalid():
    """Verify that an invalid telematics secret raises 401 Unauthorized."""
    req = DummyRequest(settings)
    settings.TELEMATICS_WEBHOOK_SECRET = "top_secret_telematics_key"

    with pytest.raises(HTTPException) as exc:
        verify_telematics_secret(req, api_key_header="wrong_secret")
    assert exc.value.status_code == 401
    assert "Invalid telematics secret" in exc.value.detail


def test_telematics_secret_verification_missing():
    """Verify that a missing telematics secret raises 401 Unauthorized."""
    req = DummyRequest(settings)
    settings.TELEMATICS_WEBHOOK_SECRET = "top_secret_telematics_key"

    with pytest.raises(HTTPException) as exc:
        verify_telematics_secret(req, api_key_header="")
    assert exc.value.status_code == 401
    assert "Invalid telematics secret" in exc.value.detail


def test_telematics_secret_verification_unconfigured():
    """Verify that if webhook secret is not configured, returns 503 Service Unavailable."""
    class EmptySettings:
        TELEMATICS_WEBHOOK_SECRET = ""
    req = DummyRequest(EmptySettings())

    with pytest.raises(HTTPException) as exc:
        verify_telematics_secret(req, api_key_header="any_secret")
    assert exc.value.status_code == 503
    assert "not configured" in exc.value.detail


# ==============================================================================
# 2. FG-SEC-033: Cross-Tenant Telemetry DoS via Duplicate IMEI Collision
# ==============================================================================

@pytest.mark.asyncio
async def test_duplicate_installed_imei_registration_rejected(db_session):
    """Verify registering a duplicate serial_number/IMEI for an active installed GPS device returns 409."""
    suffix = uuid.uuid4().hex[:6]
    c1 = Company(company_name=f"CompA {suffix}", owner_name="Owner A", mobile_number=f"ca_{suffix}")
    c2 = Company(company_name=f"CompB {suffix}", owner_name="Owner B", mobile_number=f"cb_{suffix}")
    db_session.add_all([c1, c2])
    await db_session.flush()

    v1 = Vehicle(company_id=c1.id, registration_number=f"TRK-A-{suffix}", tank_capacity=300.0)
    v2 = Vehicle(company_id=c2.id, registration_number=f"TRK-B-{suffix}", tank_capacity=300.0)
    db_session.add_all([v1, v2])
    await db_session.flush()

    u1 = User(full_name=f"Admin 1 {suffix}", mobile_number=f"910{suffix}", email=f"admin1_{suffix}@fleet.io", password_hash="hash", role=UserRole.FLEET_MANAGER, company_id=c1.id)
    u2 = User(full_name=f"Admin 2 {suffix}", mobile_number=f"911{suffix}", email=f"admin2_{suffix}@fleet.io", password_hash="hash", role=UserRole.FLEET_MANAGER, company_id=c2.id)
    db_session.add_all([u1, u2])
    await db_session.flush()

    shared_imei = f"IMEI-998877-{suffix}"

    # First registration by Company A succeeds
    p1 = HardwareAssetCreate(
        api_key="api_key_1",
        vehicle_id=v1.id,
        device_name="Primary GPS",
        serial_number=shared_imei
    )
    asset1 = await add_hardware_device(payload=p1, db=db_session, current_user=u1)
    assert asset1.serial_number == shared_imei

    # Second registration by malicious/conflicting Company B with same IMEI is rejected with 409 Conflict
    p2 = HardwareAssetCreate(
        api_key="api_key_2",
        vehicle_id=v2.id,
        device_name="Conflicting GPS",
        serial_number=shared_imei
    )
    with pytest.raises(HTTPException) as exc:
        await add_hardware_device(payload=p2, db=db_session, current_user=u2)
    assert exc.value.status_code == 409
    assert "already registered and active" in exc.value.detail


@pytest.mark.asyncio
async def test_hardware_batch_imei_resolution_prioritizes_installed(db_session):
    """Verify location_service prioritizes installed asset over uninstalled dummy asset during IMEI resolution."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Tele Co {suffix}", owner_name="Owner", mobile_number=f"tc_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-RES-{suffix}", tank_capacity=300.0)
    db_session.add(v)
    await db_session.flush()

    shared_imei = f"IMEI-RES-{suffix}"

    # Legitimate installed asset on vehicle
    legit_asset = Asset(
        business_id=f"HW-LEGIT-{suffix}",
        asset_type=AssetType.GPS_DEVICE,
        model="Teltonika FMB920",
        serial_number=shared_imei,
        current_vehicle_id=v.id,
        installation_status=AssetInstallationStatus.INSTALLED,
        operational_status=AssetOperationalStatus.OK
    )
    # Stale/uninstalled asset with same IMEI (or malicious attempt)
    dummy_asset = Asset(
        business_id=f"HW-DUMMY-{suffix}",
        asset_type=AssetType.GPS_DEVICE,
        model="Teltonika FMB920",
        serial_number=shared_imei,
        current_vehicle_id=None,
        installation_status=AssetInstallationStatus.REGISTERED,
        operational_status=AssetOperationalStatus.OK
    )
    db_session.add_all([legit_asset, dummy_asset])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    event = NormalizedHardwareEvent(
        device_imei=shared_imei,
        latitude=19.0760,
        longitude=72.8777,
        timestamp=now - timedelta(minutes=1),
        speed=45.0
    )

    res = await LocationService.process_hardware_batch(
        db=db_session,
        locations=[event],
        allow_registration_only=False
    )

    assert res["accepted"] == 1
    assert res["rejected"] == 0


# ==============================================================================
# 3. FG-SEC-034: Telemetry Timestamp Bounding (Future & Stale Rejection)
# ==============================================================================

@pytest.mark.asyncio
async def test_mobile_batch_timestamp_bounds(db_session):
    """Verify mobile GPS batch ingestion rejects points > 5min in future or > 7 days in past."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Bounds Co {suffix}", owner_name="Owner", mobile_number=f"bc_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-BND-{suffix}", tank_capacity=300.0)
    d = Driver(company_id=c.id, name="Bnd Driver", phone_number=f"907{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    # Link driver to vehicle
    v.assigned_driver_id = d.id
    await db_session.flush()

    now = datetime.now(timezone.utc)

    # 1. Valid fresh point (1 min ago)
    loc_valid = LocationPoint(
        latitude=18.5204,
        longitude=73.8567,
        timestamp=(now - timedelta(minutes=1)).isoformat()
    )
    # 2. Future point (> 5 mins future, e.g. 15 mins)
    loc_future = LocationPoint(
        latitude=18.5204,
        longitude=73.8567,
        timestamp=(now + timedelta(minutes=15)).isoformat()
    )
    # 3. Stale point (> 7 days past, e.g. 10 days)
    loc_stale = LocationPoint(
        latitude=18.5204,
        longitude=73.8567,
        timestamp=(now - timedelta(days=10)).isoformat()
    )

    res_mobile = await LocationService.process_batch(
        db=db_session,
        driver_id=d.id,
        company_id=c.id,
        locations=[loc_valid, loc_future, loc_stale]
    )

    assert res_mobile["accepted"] == 1
    assert res_mobile["rejected"] == 2
    reasons = [item.get("reason") for item in res_mobile["items"] if item.get("status") == "invalid"]
    assert "future_timestamp" in reasons
    assert "stale_timestamp" in reasons


@pytest.mark.asyncio
async def test_hardware_batch_timestamp_bounds(db_session):
    """Verify hardware GPS batch rejects points > 5min in future or > 7 days in past."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"HW Bounds {suffix}", owner_name="Owner", mobile_number=f"hb_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-HWB-{suffix}", tank_capacity=300.0)
    db_session.add(v)
    await db_session.flush()

    imei = f"IMEI-HWB-{suffix}"
    asset = Asset(
        business_id=f"HW-BND-{suffix}",
        asset_type=AssetType.GPS_DEVICE,
        model="Teltonika",
        serial_number=imei,
        current_vehicle_id=v.id,
        installation_status=AssetInstallationStatus.INSTALLED,
        operational_status=AssetOperationalStatus.OK
    )
    db_session.add(asset)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    ev_valid = NormalizedHardwareEvent(
        device_imei=imei,
        latitude=19.0,
        longitude=73.0,
        timestamp=now - timedelta(minutes=2)
    )
    ev_future = NormalizedHardwareEvent(
        device_imei=imei,
        latitude=19.0,
        longitude=73.0,
        timestamp=now + timedelta(minutes=30)
    )
    ev_stale = NormalizedHardwareEvent(
        device_imei=imei,
        latitude=19.0,
        longitude=73.0,
        timestamp=now - timedelta(days=15)
    )

    res = await LocationService.process_hardware_batch(
        db=db_session,
        locations=[ev_valid, ev_future, ev_stale],
        allow_registration_only=False
    )

    assert res["accepted"] == 1
    assert res["rejected"] == 2
    reasons = [item.get("reason") for item in res["items"] if item.get("status") == "invalid"]
    assert "future_timestamp" in reasons
    assert "stale_timestamp" in reasons


# ==============================================================================
# 4. FG-SEC-035: Trip Distance Telemetry Frozen Against Retroactive GPS Points
# ==============================================================================

@pytest.mark.asyncio
async def test_trip_distance_frozen_against_retroactive_gps(db_session):
    """Verify trip distance cannot be mutated by backdated GPS points once finalized."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Freeze Co {suffix}", owner_name="Owner", mobile_number=f"fz_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-FZ-{suffix}", tank_capacity=300.0)
    d = Driver(company_id=c.id, name="Fz Driver", phone_number=f"908{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=3)
    end_time = now - timedelta(hours=1)

    trip = Trip(
        trip_id=f"TRP-FZ-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.COMPLETED,
        actual_start_time=start_time,
        actual_end_time=end_time
    )
    db_session.add(trip)
    await db_session.flush()

    # Initial legitimate trip GPS points (~53.8 km)
    db_session.add_all([
        DriverLocation(driver_id=d.id, company_id=c.id, latitude=18.5204, longitude=73.8567, timestamp=start_time),
        DriverLocation(driver_id=d.id, company_id=c.id, latitude=18.7516, longitude=73.4067, timestamp=end_time)
    ])
    await db_session.flush()

    svc = TripCompletionService(db_session)
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)

    initial_distance = trip.actual_distance
    assert initial_distance is not None
    assert 50.0 < initial_distance < 60.0

    # Malicious actor attempts retroactive GPS point injection inside the trip window
    retroactive_pt = DriverLocation(
        driver_id=d.id,
        company_id=c.id,
        latitude=19.5000,
        longitude=74.5000,
        timestamp=start_time + timedelta(minutes=30)
    )
    db_session.add(retroactive_pt)
    await db_session.flush()

    # Trigger finalization again
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)

    # Actual distance MUST remain frozen at initial_distance
    assert trip.actual_distance == initial_distance


# ==============================================================================
# 5. FG-SEC-052: Trip State Machine Bypass Prevention & Terminal State Locking
# ==============================================================================

@pytest.mark.asyncio
async def test_terminal_trip_state_cannot_be_updated(db_session):
    """Verify trips in COMPLETED or CANCELLED terminal states cannot be updated via PATCH."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Term Co {suffix}", owner_name="Owner", mobile_number=f"tm_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-TM-{suffix}", tank_capacity=300.0)
    d = Driver(company_id=c.id, name="Tm Driver", phone_number=f"909{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    u = User(full_name=f"Dispatcher {suffix}", mobile_number=f"912{suffix}", email=f"disp_{suffix}@fleet.io", password_hash="hash", role=UserRole.DISPATCHER, company_id=c.id)
    db_session.add(u)
    await db_session.flush()

    # Completed Trip
    completed_trip = Trip(
        trip_id=f"TRP-CMP-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.COMPLETED
    )
    # Cancelled Trip
    cancelled_trip = Trip(
        trip_id=f"TRP-CNC-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.CANCELLED
    )
    db_session.add_all([completed_trip, cancelled_trip])
    await db_session.flush()

    # Attempt to revive completed trip -> 400
    with pytest.raises(HTTPException) as exc1:
        await update_trip(
            trip_id=completed_trip.id,
            payload=TripUpdated(status=TripStatus.IN_PROGRESS),
            db=db_session,
            current_user=u
        )
    assert exc1.value.status_code == 400
    assert "Cannot update a trip in terminal state 'COMPLETED'" in exc1.value.detail

    # Attempt to mutate cancelled trip -> 400
    with pytest.raises(HTTPException) as exc2:
        await update_trip(
            trip_id=cancelled_trip.id,
            payload=TripUpdated(cargo_weight=15.0),
            db=db_session,
            current_user=u
        )
    assert exc2.value.status_code == 400
    assert "Cannot update a trip in terminal state 'CANCELLED'" in exc2.value.detail


@pytest.mark.asyncio
async def test_illegal_trip_state_transition_rejected(db_session):
    """Verify invalid state transitions like CREATED -> COMPLETED are rejected."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"SM Co {suffix}", owner_name="Owner", mobile_number=f"sm_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-SM-{suffix}", tank_capacity=300.0)
    d = Driver(company_id=c.id, name="SM Driver", phone_number=f"910{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    u = User(full_name=f"Manager {suffix}", mobile_number=f"913{suffix}", email=f"mgr_{suffix}@fleet.io", password_hash="hash", role=UserRole.FLEET_MANAGER, company_id=c.id)
    db_session.add(u)
    await db_session.flush()

    trip = Trip(
        trip_id=f"TRP-SM-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.CREATED
    )
    db_session.add(trip)
    await db_session.flush()

    # Illegal jump from CREATED directly to COMPLETED -> 400
    with pytest.raises(HTTPException) as exc:
        await update_trip(
            trip_id=trip.id,
            payload=TripUpdated(status=TripStatus.COMPLETED),
            db=db_session,
            current_user=u
        )
    assert exc.value.status_code == 400
    assert "Invalid trip state transition" in exc.value.detail

    # Legal transition from CREATED to IN_PROGRESS succeeds
    res = await update_trip(
        trip_id=trip.id,
        payload=TripUpdated(status=TripStatus.IN_PROGRESS),
        db=db_session,
        current_user=u
    )
    assert res.status == TripStatus.IN_PROGRESS
