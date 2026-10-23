"""
FleetGuard — Trip Completion Telemetry Finalization Automated Tests
Validates Phase 0 foundation:
- GPS distance finalization
- Fuel consumption derivation
- Repeated finalization (idempotency)
- Partial failures (GPS-only, Fuel-only)
- Missing telemetry (never falling back to planned)
- Retry endpoint RBAC authorization and tenant isolation
- Financial regression prevention
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from database import get_db
from models.company import Company
from models.user import User, UserRole
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus
from models.trip_domain import Trip, TripStatus
from models.location_tracking import DriverLocation
from models.fuel_log import FuelLog
from models.fuel_domain import FuelTransaction, FuelTransactionType
from models.expense_domain import Expense, ExpenseStatus, ExpenseCategory
from services.trip_completion_service import TripCompletionService
from services.auth_service import get_current_user


@pytest.mark.asyncio
async def test_gps_distance_finalization(db_session):
    """Verify GPS distance calculation grounds actual_distance from DriverLocation."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"GPS Co {suffix}", owner_name="Owner", mobile_number=f"gps_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-GPS-{suffix}", tank_capacity=400.0)
    d = Driver(company_id=c.id, name="GPS Driver", phone_number=f"900{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=3)
    end_time = now - timedelta(hours=1)

    trip = Trip(
        trip_id=f"TRP-GPS-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.COMPLETED,
        actual_start_time=start_time,
        actual_end_time=end_time,
        planned_distance=200.0
    )
    db_session.add(trip)
    await db_session.flush()

    # Pune to Lonavala (~53.8 km)
    db_session.add_all([
        DriverLocation(driver_id=d.id, company_id=c.id, latitude=18.5204, longitude=73.8567, timestamp=start_time),
        DriverLocation(driver_id=d.id, company_id=c.id, latitude=18.5204, longitude=73.8567, timestamp=start_time + timedelta(minutes=5)), # duplicate
        DriverLocation(driver_id=d.id, company_id=c.id, latitude=18.7516, longitude=73.4067, timestamp=start_time + timedelta(minutes=60)),
    ])
    await db_session.flush()

    svc = TripCompletionService(db_session)
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)

    assert trip.actual_distance is not None
    assert 50.0 < trip.actual_distance < 60.0
    assert trip.actual_distance != trip.planned_distance


@pytest.mark.asyncio
async def test_fuel_consumption_derivation(db_session):
    """Verify fuel consumption derived from sensor logs and refuels."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Fuel Co {suffix}", owner_name="Owner", mobile_number=f"fl_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-FL-{suffix}", tank_capacity=400.0)
    d = Driver(company_id=c.id, name="Fuel Driver", phone_number=f"901{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=4)
    end_time = now - timedelta(hours=1)

    trip = Trip(
        trip_id=f"TRP-FL-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.COMPLETED,
        actual_start_time=start_time,
        actual_end_time=end_time,
        planned_fuel_liters=60.0
    )
    db_session.add(trip)
    await db_session.flush()

    # Start: 350L, End: 300L, Refuel during trip: 50L -> Consumed = 350 - 300 + 50 = 100L
    db_session.add_all([
        FuelLog(vehicle_id=v.id, timestamp=start_time, raw_level=350.0, filtered_level=350.0),
        FuelLog(vehicle_id=v.id, timestamp=start_time + timedelta(hours=1), raw_level=320.0, filtered_level=320.0),
        FuelLog(vehicle_id=v.id, timestamp=start_time + timedelta(hours=2), raw_level=360.0, filtered_level=360.0), # after 50L fill
        FuelLog(vehicle_id=v.id, timestamp=end_time, raw_level=300.0, filtered_level=300.0),
    ])
    db_session.add(FuelTransaction(
        company_id=c.id, vehicle_id=v.id, driver_id=d.id, trip_id=trip.id,
        transaction_type=FuelTransactionType.FILL, amount_liters=50.0,
        timestamp=start_time + timedelta(hours=1, minutes=45)
    ))
    await db_session.flush()

    svc = TripCompletionService(db_session)
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)

    assert trip.actual_fuel_liters is not None
    assert trip.actual_fuel_liters == 100.0
    assert trip.actual_fuel_liters != trip.planned_fuel_liters


@pytest.mark.asyncio
async def test_repeated_finalization_idempotency(db_session):
    """Verify repeated finalization produces identical results and does not drift."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Idem Co {suffix}", owner_name="Owner", mobile_number=f"id_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-IDEM-{suffix}", tank_capacity=400.0)
    d = Driver(company_id=c.id, name="Idem Driver", phone_number=f"902{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=2)
    end_time = now - timedelta(hours=1)

    trip = Trip(
        trip_id=f"TRP-IDEM-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.COMPLETED,
        actual_start_time=start_time,
        actual_end_time=end_time
    )
    db_session.add(trip)
    await db_session.flush()

    db_session.add_all([
        DriverLocation(driver_id=d.id, company_id=c.id, latitude=18.5204, longitude=73.8567, timestamp=start_time),
        DriverLocation(driver_id=d.id, company_id=c.id, latitude=18.7516, longitude=73.4067, timestamp=end_time),
        FuelLog(vehicle_id=v.id, timestamp=start_time, raw_level=300.0, filtered_level=300.0),
        FuelLog(vehicle_id=v.id, timestamp=end_time, raw_level=260.0, filtered_level=260.0)
    ])
    await db_session.flush()

    svc = TripCompletionService(db_session)
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)

    initial_dist = trip.actual_distance
    initial_fuel = trip.actual_fuel_liters
    assert initial_dist is not None
    assert initial_fuel == 40.0

    # Run second and third time
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)
    assert trip.actual_distance == initial_dist
    assert trip.actual_fuel_liters == initial_fuel

    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)
    assert trip.actual_distance == initial_dist
    assert trip.actual_fuel_liters == initial_fuel


@pytest.mark.asyncio
async def test_partial_failures_gps_only(db_session):
    """Verify GPS calculation succeeds even if fuel telemetry is completely missing."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"PartG Co {suffix}", owner_name="Owner", mobile_number=f"pg_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-PG-{suffix}", tank_capacity=400.0)
    d = Driver(company_id=c.id, name="PG Driver", phone_number=f"903{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=2)
    end_time = now - timedelta(hours=1)

    trip = Trip(
        trip_id=f"TRP-PG-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.COMPLETED,
        actual_start_time=start_time,
        actual_end_time=end_time
    )
    db_session.add(trip)
    await db_session.flush()

    db_session.add_all([
        DriverLocation(driver_id=d.id, company_id=c.id, latitude=18.5204, longitude=73.8567, timestamp=start_time),
        DriverLocation(driver_id=d.id, company_id=c.id, latitude=18.7516, longitude=73.4067, timestamp=end_time),
    ])
    await db_session.flush()

    svc = TripCompletionService(db_session)
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)

    assert trip.actual_distance is not None
    assert trip.actual_fuel_liters is None


@pytest.mark.asyncio
async def test_partial_failures_fuel_only(db_session):
    """Verify fuel calculation succeeds even if GPS telemetry is completely missing."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"PartF Co {suffix}", owner_name="Owner", mobile_number=f"pf_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-PF-{suffix}", tank_capacity=400.0)
    d = Driver(company_id=c.id, name="PF Driver", phone_number=f"904{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=2)
    end_time = now - timedelta(hours=1)

    trip = Trip(
        trip_id=f"TRP-PF-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.COMPLETED,
        actual_start_time=start_time,
        actual_end_time=end_time
    )
    db_session.add(trip)
    await db_session.flush()

    db_session.add_all([
        FuelLog(vehicle_id=v.id, timestamp=start_time, raw_level=300.0, filtered_level=300.0),
        FuelLog(vehicle_id=v.id, timestamp=end_time, raw_level=270.0, filtered_level=270.0),
    ])
    await db_session.flush()

    svc = TripCompletionService(db_session)
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)

    assert trip.actual_distance is None
    assert trip.actual_fuel_liters == 30.0


@pytest.mark.asyncio
async def test_missing_telemetry_isolation(db_session):
    """Verify missing telemetry leaves fields None and never fabricates or uses planned values."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Miss Co {suffix}", owner_name="Owner", mobile_number=f"ms_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-MS-{suffix}", tank_capacity=400.0)
    d = Driver(company_id=c.id, name="MS Driver", phone_number=f"905{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    trip = Trip(
        trip_id=f"TRP-MS-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.COMPLETED,
        actual_start_time=now - timedelta(hours=2),
        actual_end_time=now - timedelta(hours=1),
        planned_distance=500.0,
        planned_fuel_liters=100.0
    )
    db_session.add(trip)
    await db_session.flush()

    svc = TripCompletionService(db_session)
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)

    assert trip.actual_distance is None
    assert trip.actual_fuel_liters is None
    assert trip.planned_distance == 500.0
    assert trip.planned_fuel_liters == 100.0


@pytest.mark.asyncio
async def test_financial_regression_prevention(db_session):
    """Verify telemetry finalization never modifies financial revenues or expenses."""
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"FinReg Co {suffix}", owner_name="Owner", mobile_number=f"fr_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-FR-{suffix}", tank_capacity=400.0)
    d = Driver(company_id=c.id, name="FR Driver", phone_number=f"906{suffix}")
    db_session.add_all([v, d])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    trip = Trip(
        trip_id=f"TRP-FR-{suffix}",
        company_id=c.id,
        vehicle_id=v.id,
        driver_id=d.id,
        status=TripStatus.COMPLETED,
        actual_start_time=now - timedelta(hours=2),
        actual_end_time=now - timedelta(hours=1),
        revenue=50000.0
    )
    db_session.add(trip)
    await db_session.flush()

    exp = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=trip.id,
        business_id=f"EXP-FR-{suffix}", category=ExpenseCategory.TOLL,
        amount=2500.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(hours=1, minutes=30), origin_id=str(uuid.uuid4())
    )
    db_session.add(exp)
    await db_session.flush()

    svc = TripCompletionService(db_session)
    await svc.finalize_trip_telemetry(trip.id)
    await db_session.refresh(trip)
    await db_session.refresh(exp)

    # Telemetry should not touch financial amounts
    assert trip.revenue == 50000.0
    assert exp.amount == 2500.0
    assert exp.status == ExpenseStatus.APPROVED


@pytest.mark.asyncio
async def test_retry_endpoint_authorization_and_isolation(db_session):
    """Verify retry endpoint enforces RBAC, company scoping, and trip status validation."""
    suffix = uuid.uuid4().hex[:6]
    c1 = Company(company_name=f"Co1 {suffix}", owner_name="Owner1", mobile_number=f"c1_{suffix}")
    c2 = Company(company_name=f"Co2 {suffix}", owner_name="Owner2", mobile_number=f"c2_{suffix}")
    db_session.add_all([c1, c2])
    await db_session.flush()

    v1 = Vehicle(company_id=c1.id, registration_number=f"TRK-1-{suffix}", tank_capacity=400.0)
    db_session.add(v1)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    trip_completed = Trip(
        trip_id=f"TRP-OK-{suffix}",
        company_id=c1.id,
        vehicle_id=v1.id,
        status=TripStatus.COMPLETED,
        actual_start_time=now - timedelta(hours=2),
        actual_end_time=now - timedelta(hours=1)
    )
    trip_in_progress = Trip(
        trip_id=f"TRP-IP-{suffix}",
        company_id=c1.id,
        vehicle_id=v1.id,
        status=TripStatus.IN_PROGRESS,
        actual_start_time=now - timedelta(hours=1)
    )
    db_session.add_all([trip_completed, trip_in_progress])
    await db_session.flush()

    # User 1: COMPANY_ADMIN of Company 1
    admin_u1 = User(id=9901, company_id=c1.id, role=UserRole.COMPANY_ADMIN, is_active=True, full_name="Admin 1", mobile_number=f"adm1_{suffix}", password_hash="dummy_hash")
    # User 2: DRIVER of Company 1
    driver_u1 = User(id=9902, company_id=c1.id, role=UserRole.DRIVER, is_active=True, full_name="Driver 1", mobile_number=f"drv1_{suffix}", password_hash="dummy_hash")
    # User 3: COMPANY_ADMIN of Company 2
    admin_u2 = User(id=9903, company_id=c2.id, role=UserRole.COMPANY_ADMIN, is_active=True, full_name="Admin 2", mobile_number=f"adm2_{suffix}", password_hash="dummy_hash")
    db_session.add_all([admin_u1, driver_u1, admin_u2])
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Test 1: Driver calling retry endpoint -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: driver_u1
    with TestClient(app) as client:
        res = client.post(f"/api/v1/trips/{trip_completed.id}/retry-telemetry")
        assert res.status_code == 403

    # Test 2: Admin from another company calling Company 1 trip -> 404 Not Found
    app.dependency_overrides[get_current_user] = lambda: admin_u2
    with TestClient(app) as client:
        res = client.post(f"/api/v1/trips/{trip_completed.id}/retry-telemetry")
        assert res.status_code == 404

    # Test 3: Calling on IN_PROGRESS trip -> 400 Bad Request
    app.dependency_overrides[get_current_user] = lambda: admin_u1
    with TestClient(app) as client:
        res = client.post(f"/api/v1/trips/{trip_in_progress.id}/retry-telemetry")
        assert res.status_code == 400

    # Test 4: Authorized Admin calling completed trip -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: admin_u1
    with TestClient(app) as client:
        res = client.post(f"/api/v1/trips/{trip_completed.id}/retry-telemetry")
        assert res.status_code == 200
        assert res.json()["id"] == trip_completed.id

    app.dependency_overrides.clear()
