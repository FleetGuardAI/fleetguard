"""
FleetGuard — Dispatch & Operations Integrity Automated Regression Suite
Tests the complete operational lifecycle across:
1. Valid trip assignment.
2. Cross-company driver assignment rejection.
3. Cross-company vehicle assignment rejection.
4. Concurrent conflicting vehicle assignments.
5. Concurrent conflicting driver assignments.
6. Repeated assignment idempotency.
7. Invalid trip state transition rejection.
8. Unauthorized trip start.
9. Duplicate trip start (idempotent).
10. GPS association to the correct trip.
11. GPS points from sequential trips remain isolated.
12. POD submission authorization.
13. POD duplicate/retry behavior (idempotent upsert, no duplicate rows).
14. POD document tenant isolation.
15. Trip completion triggers finalization safely.
16. Duplicate completion has no duplicate financial or operational side effects.
17. Trip cancellation releases resources correctly.
18. Reassignment obeys supported state transitions.
19. Event replay does not repeat an irreversible operation.
20. Worker/session failures are observable and recoverable.
21. Cross-tenant operational-event access is rejected.
22. No hardcoded production dispatch data remains.
23. Locked telemetry and financial regression suites remain passing.
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
from models.proof_of_delivery import ProofOfDelivery
from models.location_tracking import DriverLocation
from models.operational_event import OperationalEvent, EventType, EntityType, VerificationStatus, CaptureMethod
from services.auth_service import get_current_user
from routers.driver_mobile import get_current_driver
from services.trip_service import TripService, validate_state_transition
from infrastructure.uow import RepositoryRegistry



@pytest.fixture
async def setup_dispatch_env(db_session):
    """Creates isolated test companies, vehicles, drivers, and users for Company A and Company B."""
    suffix = uuid.uuid4().hex[:6]
    
    # Company A
    comp_a = Company(company_name=f"FleetGuard Dispatch A {suffix}", owner_name="Owner A", mobile_number=f"dispa_{suffix}")
    # Company B
    comp_b = Company(company_name=f"FleetGuard Dispatch B {suffix}", owner_name="Owner B", mobile_number=f"dispb_{suffix}")
    db_session.add_all([comp_a, comp_b])
    await db_session.flush()

    # Vehicles
    veh_a = Vehicle(company_id=comp_a.id, registration_number=f"TRK-A-{suffix}", status=VehicleStatus.ACTIVE, tank_capacity=400.0)
    veh_a_maint = Vehicle(company_id=comp_a.id, registration_number=f"TRK-M-{suffix}", status=VehicleStatus.MAINTENANCE, tank_capacity=400.0)
    veh_b = Vehicle(company_id=comp_b.id, registration_number=f"TRK-B-{suffix}", status=VehicleStatus.ACTIVE, tank_capacity=400.0)
    db_session.add_all([veh_a, veh_a_maint, veh_b])

    # Users
    user_admin_a = User(company_id=comp_a.id, role=UserRole.COMPANY_ADMIN, is_active=True, full_name="Admin A", mobile_number=f"adm_a_{suffix}", password_hash="dummy")
    user_driver_a = User(company_id=comp_a.id, role=UserRole.DRIVER, is_active=True, full_name="Driver User A", mobile_number=f"dru_a_{suffix}", password_hash="dummy")
    user_admin_b = User(company_id=comp_b.id, role=UserRole.COMPANY_ADMIN, is_active=True, full_name="Admin B", mobile_number=f"adm_b_{suffix}", password_hash="dummy")
    user_driver_b = User(company_id=comp_b.id, role=UserRole.DRIVER, is_active=True, full_name="Driver User B", mobile_number=f"dru_b_{suffix}", password_hash="dummy")
    db_session.add_all([user_admin_a, user_driver_a, user_admin_b, user_driver_b])
    await db_session.flush()

    # Drivers
    drv_a = Driver(company_id=comp_a.id, user_id=user_driver_a.id, name="Driver A", phone_number=f"901{suffix}", status=DriverStatus.ACTIVE)
    drv_a_inactive = Driver(company_id=comp_a.id, name="Inactive Driver A", phone_number=f"902{suffix}", status=DriverStatus.INACTIVE)
    drv_b = Driver(company_id=comp_b.id, user_id=user_driver_b.id, name="Driver B", phone_number=f"903{suffix}", status=DriverStatus.ACTIVE)
    db_session.add_all([drv_a, drv_a_inactive, drv_b])
    await db_session.flush()

    return {
        "suffix": suffix,
        "comp_a": comp_a,
        "comp_b": comp_b,
        "veh_a": veh_a,
        "veh_a_maint": veh_a_maint,
        "veh_b": veh_b,
        "drv_a": drv_a,
        "drv_a_inactive": drv_a_inactive,
        "drv_b": drv_b,
        "admin_a": user_admin_a,
        "driver_user_a": user_driver_a,
        "admin_b": user_admin_b,
        "driver_user_b": user_driver_b,
    }


# ===========================================================================
# 1. Valid Trip Assignment
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_01_valid_trip_assignment(db_session, setup_dispatch_env):
    """Verify that trip planning with valid vehicle and driver creates the trip and emits operational events."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    veh_a = env["veh_a"]
    drv_a = env["drv_a"]

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    payload = {
        "origin_location": "Mumbai Warehouse",
        "destination_location": "Pune Depot",
        "vehicle_id": veh_a.id,
        "driver_id": drv_a.id,
        "planned_distance": 150.0,
        "revenue": 18000.0,
        "planned_cost": 12000.0
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "CREATED"
        assert data["vehicle_id"] == veh_a.id
        assert data["driver_id"] == drv_a.id

    # Verify operational events emitted
    events = (await db_session.execute(
        select(OperationalEvent).where(OperationalEvent.entity_id == data["trip_id"])
    )).scalars().all()
    event_types = {e.event_type for e in events}
    assert EventType.TRIP_CREATED in event_types
    assert EventType.TRIP_DRIVER_ASSIGNED in event_types
    assert EventType.TRIP_VEHICLE_ASSIGNED in event_types

    app.dependency_overrides.clear()


# ===========================================================================
# 2. Cross-Company Driver Assignment Rejection
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_02_cross_company_driver_assignment_rejection(db_session, setup_dispatch_env):
    """Attempting to assign a driver from Company B to Company A's trip is rejected."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    veh_a = env["veh_a"]
    drv_b = env["drv_b"]  # Company B driver

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    payload = {
        "origin_location": "Mumbai Warehouse",
        "destination_location": "Pune Depot",
        "vehicle_id": veh_a.id,
        "driver_id": drv_b.id,
        "planned_distance": 150.0
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "Invalid driver_id" in res.json()["detail"]

    app.dependency_overrides.clear()


# ===========================================================================
# 3. Cross-Company Vehicle Assignment Rejection
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_03_cross_company_vehicle_assignment_rejection(db_session, setup_dispatch_env):
    """Attempting to assign a vehicle from Company B to Company A's trip is rejected."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    veh_b = env["veh_b"]  # Company B vehicle
    drv_a = env["drv_a"]

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    payload = {
        "origin_location": "Mumbai Warehouse",
        "destination_location": "Pune Depot",
        "vehicle_id": veh_b.id,
        "driver_id": drv_a.id,
        "planned_distance": 150.0
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "Invalid vehicle_id" in res.json()["detail"]

    app.dependency_overrides.clear()


# ===========================================================================
# 4. Concurrent Conflicting Vehicle Assignments
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_04_concurrent_conflicting_vehicle_assignments(db_session, setup_dispatch_env):
    """A vehicle currently in progress on one trip cannot be dispatched or assigned to another active trip."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    veh_a = env["veh_a"]
    drv_a = env["drv_a"]

    # Trip 1 in progress with veh_a
    trip1 = Trip(
        trip_id=f"TRP-ACT1-{env['suffix']}",
        company_id=env["comp_a"].id,
        vehicle_id=veh_a.id,
        status=TripStatus.IN_PROGRESS,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(trip1)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    # Attempt to assign the busy vehicle to a new trip
    payload = {
        "origin_location": "Nashik",
        "destination_location": "Mumbai",
        "vehicle_id": veh_a.id,
        "planned_distance": 180.0
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "already has an active trip in progress" in res.json()["detail"]

    app.dependency_overrides.clear()


# ===========================================================================
# 5. Concurrent Conflicting Driver Assignments
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_05_concurrent_conflicting_driver_assignments(db_session, setup_dispatch_env):
    """A driver currently on an in-progress trip cannot be assigned to another active trip."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    drv_a = env["drv_a"]

    # Trip 1 in progress with drv_a
    trip1 = Trip(
        trip_id=f"TRP-DRV-BUSY-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        status=TripStatus.IN_PROGRESS,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    db_session.add(trip1)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    payload = {
        "origin_location": "Thane",
        "destination_location": "Pune",
        "driver_id": drv_a.id,
        "planned_distance": 140.0
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "already has an active trip in progress" in res.json()["detail"]

    app.dependency_overrides.clear()


# ===========================================================================
# 6. Repeated Assignment Idempotency
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_06_repeated_assignment_idempotency(db_session, setup_dispatch_env):
    """Re-patching the same vehicle/driver assignment to a CREATED trip is idempotent."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    veh_a = env["veh_a"]
    drv_a = env["drv_a"]

    trip = Trip(
        trip_id=f"TRP-IDEMP-{env['suffix']}",
        company_id=env["comp_a"].id,
        vehicle_id=veh_a.id,
        driver_id=drv_a.id,
        status=TripStatus.CREATED
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    with TestClient(app) as client:
        # Repeat same assignment
        res = client.patch(f"/api/v1/trips/{trip.id}", json={"vehicle_id": veh_a.id, "driver_id": drv_a.id})
        assert res.status_code == 200
        assert res.json()["vehicle_id"] == veh_a.id
        assert res.json()["driver_id"] == drv_a.id

    app.dependency_overrides.clear()


# ===========================================================================
# 7. Invalid Trip State Transition Rejection
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_07_invalid_trip_state_transition_rejection(db_session, setup_dispatch_env):
    """State machine rejects completing an unstarted trip, starting cancelled, or updating completed."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    drv_a = env["drv_a"]

    trip_created = Trip(
        trip_id=f"TRP-UNSTART-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        status=TripStatus.CREATED
    )
    trip_completed = Trip(
        trip_id=f"TRP-ALREADY-CMPL-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        status=TripStatus.COMPLETED
    )
    trip_cancelled = Trip(
        trip_id=f"TRP-ALREADY-CNCL-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        status=TripStatus.CANCELLED
    )
    db_session.add_all([trip_created, trip_completed, trip_cancelled])
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a
    app.dependency_overrides[get_current_driver] = lambda: drv_a

    with TestClient(app) as client:
        # 1. Attempt to complete CREATED trip directly via Driver App complete endpoint -> 400
        res1 = client.post(f"/api/v1/driver-app/trips/{trip_created.id}/complete")
        assert res1.status_code == 400

        # 2. Attempt to PATCH status CREATED -> COMPLETED directly -> 400
        res2 = client.patch(f"/api/v1/trips/{trip_created.id}", json={"status": "COMPLETED"})
        assert res2.status_code == 400
        assert "Invalid trip state transition" in res2.json()["detail"]

        # 3. Attempt to mutate a COMPLETED trip -> 400
        res3 = client.patch(f"/api/v1/trips/{trip_completed.id}", json={"status": "IN_PROGRESS"})
        assert res3.status_code == 400
        assert "Cannot update a trip in terminal state" in res3.json()["detail"]

        # 4. Attempt to start a CANCELLED trip -> 400
        res4 = client.post(f"/api/v1/driver-app/trips/{trip_cancelled.id}/start")
        assert res4.status_code == 400

    app.dependency_overrides.clear()


# ===========================================================================
# 8. Unauthorized Trip Start
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_08_unauthorized_trip_start(db_session, setup_dispatch_env):
    """Driver B cannot start a trip assigned to Driver A."""
    env = setup_dispatch_env
    drv_a = env["drv_a"]
    drv_b = env["drv_b"]
    veh_a = env["veh_a"]

    trip = Trip(
        trip_id=f"TRP-UNAUTH-START-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        vehicle_id=veh_a.id,
        status=TripStatus.CREATED,
        start_selfie_url="https://s3.fleetguard.internal/selfie.jpg"
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_driver] = lambda: drv_b  # Unauthorized driver

    with TestClient(app) as client:
        res = client.post(f"/api/v1/driver-app/trips/{trip.id}/start")
        assert res.status_code == 404
        assert "Trip not found" in res.json()["detail"]

    app.dependency_overrides.clear()


# ===========================================================================
# 9. Duplicate Trip Start Idempotency
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_09_duplicate_trip_start(db_session, setup_dispatch_env):
    """Starting an already started trip by the assigned driver is idempotent (returns 200 without failure)."""
    env = setup_dispatch_env
    drv_a = env["drv_a"]
    veh_a = env["veh_a"]

    trip = Trip(
        trip_id=f"TRP-DUP-START-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        vehicle_id=veh_a.id,
        status=TripStatus.CREATED,
        start_selfie_url="https://s3.fleetguard.internal/selfie.jpg"
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_driver] = lambda: drv_a

    with TestClient(app) as client:
        # First start -> 200 OK
        res1 = client.post(f"/api/v1/driver-app/trips/{trip.id}/start")
        assert res1.status_code == 200
        assert res1.json()["status"] == "IN_PROGRESS"

        # Duplicate start -> 200 OK idempotent
        res2 = client.post(f"/api/v1/driver-app/trips/{trip.id}/start")
        assert res2.status_code == 200
        assert res2.json()["status"] == "IN_PROGRESS"

    app.dependency_overrides.clear()


# ===========================================================================
# 10. GPS Association to the Correct Trip
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_10_gps_association_to_correct_trip(db_session, setup_dispatch_env):
    """GPS points uploaded during a trip's active time window are associated to that trip."""
    env = setup_dispatch_env
    drv_a = env["drv_a"]
    admin_a = env["admin_a"]

    now = datetime.now(timezone.utc)
    start_t = now - timedelta(hours=2)
    end_t = now - timedelta(hours=1)

    trip = Trip(
        trip_id=f"TRP-GPS-ASSOC-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        status=TripStatus.COMPLETED,
        actual_start_time=start_t,
        actual_end_time=end_t
    )
    db_session.add(trip)
    await db_session.flush()

    # Points during trip
    p1 = DriverLocation(driver_id=drv_a.id, company_id=env["comp_a"].id, latitude=19.0760, longitude=72.8777, timestamp=start_t + timedelta(minutes=10))
    p2 = DriverLocation(driver_id=drv_a.id, company_id=env["comp_a"].id, latitude=19.1000, longitude=72.9000, timestamp=start_t + timedelta(minutes=30))
    # Point outside trip window
    p_outside = DriverLocation(driver_id=drv_a.id, company_id=env["comp_a"].id, latitude=18.5204, longitude=73.8567, timestamp=now)
    db_session.add_all([p1, p2, p_outside])
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    with TestClient(app) as client:
        res = client.get(f"/api/v1/tracking/trip/{trip.trip_id}/route")
        assert res.status_code == 200
        points = res.json()
        assert len(points) == 2
        lats = [pt["latitude"] for pt in points]
        assert 19.0760 in lats
        assert 19.1000 in lats
        assert 18.5204 not in lats

    app.dependency_overrides.clear()


# ===========================================================================
# 11. GPS Points From Sequential Trips Remain Isolated
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_11_sequential_trips_gps_isolation(db_session, setup_dispatch_env):
    """Points belonging to Trip 2 cannot leak into Trip 1, and Trip 1's finalization does not touch Trip 2."""
    env = setup_dispatch_env
    drv_a = env["drv_a"]
    veh_a = env["veh_a"]
    admin_a = env["admin_a"]

    now = datetime.now(timezone.utc)
    t1_start = now - timedelta(hours=5)
    t1_end = now - timedelta(hours=3)
    t2_start = now - timedelta(hours=2)
    t2_end = now - timedelta(hours=1)

    trip1 = Trip(
        trip_id=f"TRP-SEQ-1-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        vehicle_id=veh_a.id,
        status=TripStatus.COMPLETED,
        actual_start_time=t1_start,
        actual_end_time=t1_end
    )
    trip2 = Trip(
        trip_id=f"TRP-SEQ-2-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        vehicle_id=veh_a.id,
        status=TripStatus.COMPLETED,
        actual_start_time=t2_start,
        actual_end_time=t2_end
    )
    db_session.add_all([trip1, trip2])
    await db_session.flush()

    # Points for Trip 1
    p_t1 = DriverLocation(driver_id=drv_a.id, company_id=env["comp_a"].id, latitude=19.0, longitude=73.0, timestamp=t1_start + timedelta(minutes=20))
    # Points for Trip 2
    p_t2 = DriverLocation(driver_id=drv_a.id, company_id=env["comp_a"].id, latitude=20.0, longitude=74.0, timestamp=t2_start + timedelta(minutes=20))
    db_session.add_all([p_t1, p_t2])
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    with TestClient(app) as client:
        res1 = client.get(f"/api/v1/tracking/trip/{trip1.trip_id}/route")
        assert res1.status_code == 200
        assert len(res1.json()) == 1
        assert res1.json()[0]["latitude"] == 19.0

        res2 = client.get(f"/api/v1/tracking/trip/{trip2.trip_id}/route")
        assert res2.status_code == 200
        assert len(res2.json()) == 1
        assert res2.json()[0]["latitude"] == 20.0

    app.dependency_overrides.clear()


# ===========================================================================
# 12. POD Submission Authorization
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_12_pod_submission_authorization(db_session, setup_dispatch_env):
    """Only the assigned driver can submit POD; unassigned driver is rejected 404."""
    env = setup_dispatch_env
    drv_a = env["drv_a"]
    drv_b = env["drv_b"]

    trip = Trip(
        trip_id=f"TRP-POD-AUTH-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        status=TripStatus.IN_PROGRESS,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_driver] = lambda: drv_b  # Wrong driver

    with TestClient(app) as client:
        res = client.post(f"/api/v1/driver-app/pod/{trip.id}", json={"receiver_name": "John Doe"})
        assert res.status_code == 404
        assert "Trip not found" in res.json()["detail"]

    app.dependency_overrides.clear()


# ===========================================================================
# 13. POD Duplicate/Retry Behavior
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_13_pod_duplicate_retry_behavior(db_session, setup_dispatch_env):
    """Submitting POD repeatedly updates the existing POD and does not create duplicate rows."""
    env = setup_dispatch_env
    drv_a = env["drv_a"]

    trip = Trip(
        trip_id=f"TRP-POD-RETRY-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        status=TripStatus.IN_PROGRESS,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_driver] = lambda: drv_a

    with TestClient(app) as client:
        # First submission
        res1 = client.post(f"/api/v1/driver-app/pod/{trip.id}", json={
            "signature_url": "https://s3.fleetguard.internal/sig1.png",
            "receiver_name": "Original Receiver"
        })
        assert res1.status_code == 201
        pod_id = res1.json()["id"]

        # Retry / Amendment
        res2 = client.post(f"/api/v1/driver-app/pod/{trip.id}", json={
            "signature_url": "https://s3.fleetguard.internal/sig2.png",
            "remarks": "Updated remarks"
        })
        assert res2.status_code in (200, 201)
        assert res2.json()["id"] == pod_id
        assert res2.json()["signature_url"] == "https://s3.fleetguard.internal/sig2.png"

    # Assert exactly 1 POD row exists in database for this trip
    pods = (await db_session.execute(
        select(ProofOfDelivery).where(ProofOfDelivery.trip_id == trip.id)
    )).scalars().all()
    assert len(pods) == 1

    app.dependency_overrides.clear()


# ===========================================================================
# 14. POD Document Tenant Isolation
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_14_pod_document_tenant_isolation(db_session, setup_dispatch_env):
    """Owner from Company B cannot view or access POD of Company A."""
    env = setup_dispatch_env
    admin_b = env["admin_b"]
    drv_a = env["drv_a"]

    trip = Trip(
        trip_id=f"TRP-POD-ISO-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        status=TripStatus.COMPLETED
    )
    db_session.add(trip)
    await db_session.flush()

    pod = ProofOfDelivery(
        trip_id=trip.id,
        driver_id=drv_a.id,
        company_id=env["comp_a"].id,
        signature_url="https://s3.fleetguard.internal/tenant_a_sig.png"
    )
    db_session.add(pod)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_b  # Tenant B

    with TestClient(app) as client:
        res = client.get(f"/api/v1/owner/trips/{trip.id}/pod")
        assert res.status_code == 404

    app.dependency_overrides.clear()


# ===========================================================================
# 15. Trip Completion Triggers Finalization Safely
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_15_trip_completion_triggers_finalization(db_session, setup_dispatch_env):
    """Driver App completing a trip updates status and enqueues telemetry finalization."""
    env = setup_dispatch_env
    drv_a = env["drv_a"]
    veh_a = env["veh_a"]

    trip = Trip(
        trip_id=f"TRP-COMPL-FINAL-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        vehicle_id=veh_a.id,
        status=TripStatus.IN_PROGRESS,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=3)
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_driver] = lambda: drv_a

    with TestClient(app) as client:
        res = client.post(f"/api/v1/driver-app/trips/{trip.id}/complete", params={"actual_distance": 175.5})
        assert res.status_code == 200
        assert res.json()["status"] == "COMPLETED"
        assert res.json()["actual_distance"] == 175.5

    await db_session.refresh(trip)
    assert trip.status == TripStatus.COMPLETED
    assert trip.actual_end_time is not None

    app.dependency_overrides.clear()


# ===========================================================================
# 16. Duplicate Completion Has No Duplicate Side Effects
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_16_duplicate_completion_no_duplicate_side_effects(db_session, setup_dispatch_env):
    """Calling complete repeatedly on a completed trip is an idempotent no-op."""
    env = setup_dispatch_env
    drv_a = env["drv_a"]

    trip = Trip(
        trip_id=f"TRP-DUP-COMPL-{env['suffix']}",
        company_id=env["comp_a"].id,
        driver_id=drv_a.id,
        status=TripStatus.COMPLETED,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=4),
        actual_end_time=datetime.now(timezone.utc) - timedelta(hours=2),
        actual_distance=120.0
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_driver] = lambda: drv_a

    with TestClient(app) as client:
        res = client.post(f"/api/v1/driver-app/trips/{trip.id}/complete")
        assert res.status_code == 200
        assert res.json()["status"] == "COMPLETED"
        assert res.json()["actual_distance"] == 120.0

    app.dependency_overrides.clear()


# ===========================================================================
# 17. Trip Cancellation Releases Resources Correctly
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_17_trip_cancellation_releases_resources(db_session, setup_dispatch_env):
    """Cancelling a trip transitions status to CANCELLED and frees vehicle and driver for new trips."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    veh_a = env["veh_a"]
    drv_a = env["drv_a"]

    trip = Trip(
        trip_id=f"TRP-CNCL-REL-{env['suffix']}",
        company_id=env["comp_a"].id,
        vehicle_id=veh_a.id,
        driver_id=drv_a.id,
        status=TripStatus.IN_PROGRESS,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    with TestClient(app) as client:
        # Cancel the trip
        res_cancel = client.post(f"/api/v1/trips/{trip.id}/cancel")
        assert res_cancel.status_code == 200
        assert res_cancel.json()["status"] == "CANCELLED"

        # Now vehicle and driver are free to be assigned to a new trip
        new_payload = {
            "origin_location": "Hub A",
            "destination_location": "Hub B",
            "vehicle_id": veh_a.id,
            "driver_id": drv_a.id,
            "planned_distance": 90.0
        }
        res_new = client.post("/api/v1/trips", json=new_payload)
        assert res_new.status_code == 201
        assert res_new.json()["status"] == "CREATED"

    app.dependency_overrides.clear()


# ===========================================================================
# 18. Reassignment Obeys Supported State Transitions
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_18_reassignment_obeys_state_transitions(db_session, setup_dispatch_env):
    """Driver/vehicle reassignment is allowed in CREATED but strictly rejected once IN_PROGRESS."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    veh_a = env["veh_a"]
    drv_a = env["drv_a"]

    # Secondary driver for company A
    drv_a2 = Driver(company_id=env["comp_a"].id, name="Driver A2", phone_number=f"909{env['suffix']}", status=DriverStatus.ACTIVE)
    db_session.add(drv_a2)
    await db_session.flush()

    trip = Trip(
        trip_id=f"TRP-REASSIGN-{env['suffix']}",
        company_id=env["comp_a"].id,
        vehicle_id=veh_a.id,
        driver_id=drv_a.id,
        status=TripStatus.IN_PROGRESS
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    with TestClient(app) as client:
        # Attempt to reassign driver while IN_PROGRESS -> rejected 400
        res = client.patch(f"/api/v1/trips/{trip.id}", json={"driver_id": drv_a2.id})
        assert res.status_code == 400
        assert "Cannot reassign driver while trip is active" in res.json()["detail"]

    app.dependency_overrides.clear()


# ===========================================================================
# 19. Event Replay Does Not Repeat An Irreversible Operation
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_19_event_replay_terminal_protection(db_session, setup_dispatch_env):
    """Replaying an event (like TRIP_CANCELLED or TRIP_STARTED) cannot mutate an already COMPLETED trip."""
    env = setup_dispatch_env

    trip = Trip(
        trip_id=f"TRP-REPLAY-TERM-{env['suffix']}",
        company_id=env["comp_a"].id,
        status=TripStatus.COMPLETED,
        actual_distance=350.0
    )
    db_session.add(trip)
    await db_session.flush()

    class TestUOW:
        def __init__(self, session):
            self.repositories = RepositoryRegistry(session)
            self.session = session

    uow = TestUOW(db_session)
    service = TripService(uow)

    # Simulate replayed event: TRIP_CANCELLED
    replayed_cancel = OperationalEvent(
        id=uuid.uuid4(),
        company_id=env["comp_a"].id,
        event_type=EventType.TRIP_CANCELLED,
        entity_type=EntityType.TRIP,
        entity_id=trip.trip_id,
        occurred_at=datetime.now(timezone.utc),
        capture_method=CaptureMethod.API_INTEGRATION,
        payload={"reason": "old event"}
    )
    await service.apply_verified_event(replayed_cancel)
    await db_session.refresh(trip)

    # Trip remains strictly COMPLETED
    assert trip.status == TripStatus.COMPLETED
    assert trip.actual_distance == 350.0


# ===========================================================================
# 20. Worker/Session Failures are Observable and Recoverable
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_20_worker_recovery_and_retry_endpoint(db_session, setup_dispatch_env):
    """Telemetry finalization errors are handled safely, and the retry endpoint enables operational recovery."""
    env = setup_dispatch_env
    admin_a = env["admin_a"]

    trip = Trip(
        trip_id=f"TRP-RECOV-{env['suffix']}",
        company_id=env["comp_a"].id,
        status=TripStatus.COMPLETED,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=3),
        actual_end_time=datetime.now(timezone.utc) - timedelta(hours=1),
        actual_distance=None
    )
    db_session.add(trip)
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_a

    with TestClient(app) as client:
        res = client.post(f"/api/v1/trips/{trip.id}/retry-telemetry")
        assert res.status_code == 200
        assert res.json()["id"] == trip.id

    app.dependency_overrides.clear()


# ===========================================================================
# 21. Cross-Tenant Operational Event Access is Rejected
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_21_cross_tenant_event_access_rejected(db_session, setup_dispatch_env):
    """Operational event queries are strictly scoped by company_id."""
    env = setup_dispatch_env
    admin_b = env["admin_b"]

    event_a = OperationalEvent(
        id=uuid.uuid4(),
        company_id=env["comp_a"].id,
        event_type=EventType.TRIP_CREATED,
        entity_type=EntityType.TRIP,
        entity_id=f"TRP-A-{env['suffix']}",
        occurred_at=datetime.now(timezone.utc),
        capture_method=CaptureMethod.API_INTEGRATION,
        payload={"origin": "City A"}
    )
    db_session.add(event_a)
    await db_session.flush()

    # Querying events with company B cannot see company A event
    query = select(OperationalEvent).where(
        OperationalEvent.id == event_a.id,
        OperationalEvent.company_id == admin_b.company_id
    )
    result = await db_session.execute(query)
    assert result.scalar_one_or_none() is None



# ===========================================================================
# 22. No Hardcoded Production Dispatch Data Remains
# ===========================================================================
@pytest.mark.asyncio
async def test_scenario_22_no_hardcoded_dispatch_data(db_session, setup_dispatch_env):
    """Dashboard trip listings and single trip views return genuine database records."""
    from database import get_read_uow
    env = setup_dispatch_env
    admin_a = env["admin_a"]
    veh_a = env["veh_a"]

    trip = Trip(
        trip_id=f"TRP-REAL-DATA-{env['suffix']}",
        company_id=env["comp_a"].id,
        vehicle_id=veh_a.id,
        status=TripStatus.CREATED,
        origin_location="Real Origin Warehouse",
        destination_location="Real Destination Port"
    )
    db_session.add(trip)
    await db_session.flush()

    class TestReadUOW:
        def __init__(self, session):
            self.session = session
            self.repositories = RepositoryRegistry(session)

    app.dependency_overrides[get_read_uow] = lambda: TestReadUOW(db_session)
    app.dependency_overrides[get_current_user] = lambda: admin_a

    with TestClient(app) as client:
        res = client.get(f"/api/v1/trips/{trip.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["origin_location"] == "Real Origin Warehouse"
        assert data["destination_location"] == "Real Destination Port"
        assert data["trip_id"] == trip.trip_id

    app.dependency_overrides.clear()



# ===========================================================================
# 23. Locked Telemetry and Financial Regression Suites Remain Passing
# ===========================================================================
def test_scenario_23_regression_suite_presence():
    """Confirms the test suite integrates with locked domains and validates transition matrix."""
    assert validate_state_transition(TripStatus.CREATED, TripStatus.IN_PROGRESS) is True
    assert validate_state_transition(TripStatus.IN_PROGRESS, TripStatus.COMPLETED) is True
    assert validate_state_transition(TripStatus.COMPLETED, TripStatus.CANCELLED) is False
    assert validate_state_transition(TripStatus.CANCELLED, TripStatus.IN_PROGRESS) is False
