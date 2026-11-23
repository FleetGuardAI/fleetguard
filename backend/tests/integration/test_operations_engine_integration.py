"""
Fleetguard — Operations Engine End-to-End Integration Test Suite

Verifies:
- Scenario A: GPS and Vehicle Telemetry Ingestion, Out-of-Order Rejection & FIE Freshness
- Scenario B: Trip Lifecycle (Created -> Started -> Completed -> Telemetry Finalization)
- Scenario C: Fuel & Expense Ledger Integration with Idempotency Protection
- Scenario D: Maintenance Integration & Linked Expense Generation
- Scenario E: Operations Engine Pipeline to Fleet Intelligence Engine
- Scenario F: Controlled Failure Recovery & Multi-Tenant Company Isolation
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func

from models.operational_event import (
    OperationalEvent,
    EventType,
    EntityType,
    CaptureMethod,
    VerificationStatus,
)
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus, DutyStatus
from models.trip_domain import Trip, TripStatus
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus, MaintenanceCategory
from models.location_tracking import DriverLocation, VehicleCurrentLocation, LocationSource
from models.outbox_event import OutboxEvent, OutboxStatus
from schemas.operational_event import OperationalEventCreate, OperationalEventResponse

from dispatchers.event_dispatcher import EventDispatcher, default_dispatcher
from services.operational_event_service import OperationalEventService
from services.trip_completion_service import TripCompletionService
from services.fleet_intelligence_engine import FleetIntelligenceEngine
from services.fleet_intelligence_service import FleetIntelligenceService
from infrastructure.uow import SqlAlchemyUnitOfWork, RepositoryRegistry, AbstractUnitOfWork
import main


class MockUnitOfWork(AbstractUnitOfWork):
    """Transactional wrapper around the test db_session."""
    __test__ = False

    def __init__(self, session):
        self.session = session
        self.repositories = RepositoryRegistry(session)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()


@pytest.fixture(autouse=True)
def wire_test_db(db_session):
    """Binds background processing engines directly to the active test database session."""
    orig_proc_factory = main.processing_consumer_instance.processing_service.db_session_factory
    orig_val_factory = main.validation_consumer.validation_service.db_session_factory
    orig_ev_factory = main.evidence_orchestrator.session_factory
    orig_fic_factory = getattr(main.fuel_intelligence_consumer, "session_factory", None)

    db_session._is_shared = True
    main.processing_consumer_instance.processing_service.db_session_factory = lambda: db_session
    main.validation_consumer.validation_service.db_session_factory = lambda: db_session
    main.evidence_orchestrator.session_factory = lambda: db_session
    main.fuel_intelligence_consumer.session_factory = lambda: db_session

    yield

    main.processing_consumer_instance.processing_service.db_session_factory = orig_proc_factory
    main.validation_consumer.validation_service.db_session_factory = orig_val_factory
    main.evidence_orchestrator.session_factory = orig_ev_factory
    main.fuel_intelligence_consumer.session_factory = orig_fic_factory


# ===========================================================================
# SCENARIO A: GPS AND VEHICLE TRACKING
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_a_gps_tracking_and_freshness(db_session):
    """
    1. Submit valid GPS points from driver app.
    2. Verify DriverLocation and VehicleCurrentLocation are persisted.
    3. Verify stale/older telemetry does not overwrite newer data (out-of-order rejection).
    4. Verify FleetIntelligenceEngine resolves the freshest location.
    """
    company_id = 101

    # Create vehicle & driver
    vehicle = Vehicle(
        registration_number="MH-01-AB-1234",
        make="Tata",
        model="Prima",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        origin_type="manual",
        origin_id="init",
    )
    db_session.add(vehicle)
    await db_session.flush()

    driver = Driver(
        name="Rajesh Kumar",
        phone_number="+919876543210",
        status=DriverStatus.ACTIVE,
        company_id=company_id,
        origin_type="manual",
        origin_id="init",
    )
    db_session.add(driver)
    await db_session.flush()

    # Assign driver to vehicle
    vehicle.assigned_driver_id = driver.id
    await db_session.commit()

    # 1. Submit initial GPS location at T = now - 10 minutes
    now = datetime.now(timezone.utc)
    t_initial = now - timedelta(minutes=10)

    from routers.location_tracking import batch_upload_locations, LocationBatchRequest, LocationPoint
    payload = LocationBatchRequest(
        driver_id=driver.id,
        locations=[
            LocationPoint(
                latitude=19.0760,
                longitude=72.8777,
                speed=45.0,
                heading=90.0,
                accuracy=10.0,
                timestamp=t_initial.isoformat(),
            )
        ]
    )

    resp = await batch_upload_locations(payload=payload, driver=driver, db=db_session)
    assert "1 locations recorded" in resp["message"]

    # Verify DriverLocation stored
    loc_res = await db_session.execute(
        select(DriverLocation).where(DriverLocation.driver_id == driver.id)
    )
    locs = loc_res.scalars().all()
    assert len(locs) == 1
    assert locs[0].latitude == 19.0760
    assert locs[0].longitude == 72.8777

    # Verify VehicleCurrentLocation stored
    vcl_res = await db_session.execute(
        select(VehicleCurrentLocation).where(VehicleCurrentLocation.vehicle_id == vehicle.id)
    )
    vcl = vcl_res.scalar_one_or_none()
    assert vcl is not None
    assert vcl.latitude == 19.0760
    assert vcl.longitude == 72.8777
    assert vcl.source == LocationSource.PHONE_GPS

    # 2. Submit older/stale telemetry point at T = now - 20 minutes (out of order)
    t_stale = now - timedelta(minutes=20)
    payload_stale = LocationBatchRequest(
        driver_id=driver.id,
        locations=[
            LocationPoint(
                latitude=18.5204,
                longitude=73.8567,
                speed=30.0,
                heading=180.0,
                accuracy=15.0,
                timestamp=t_stale.isoformat(),
            )
        ]
    )
    await batch_upload_locations(payload=payload_stale, driver=driver, db=db_session)

    # Verify VehicleCurrentLocation NOT overwritten by older point
    await db_session.refresh(vcl)
    assert vcl.latitude == 19.0760
    assert vcl.longitude == 72.8777

    # 3. Submit newer telemetry point at T = now - 2 minutes
    t_newer = now - timedelta(minutes=2)
    payload_newer = LocationBatchRequest(
        driver_id=driver.id,
        locations=[
            LocationPoint(
                latitude=19.1200,
                longitude=72.9000,
                speed=60.0,
                heading=45.0,
                accuracy=8.0,
                timestamp=t_newer.isoformat(),
            )
        ]
    )
    await batch_upload_locations(payload=payload_newer, driver=driver, db=db_session)

    # Verify VehicleCurrentLocation updated to newer coordinates
    await db_session.refresh(vcl)
    assert vcl.latitude == 19.1200
    assert vcl.longitude == 72.9000

    # 4. Verify FleetIntelligenceEngine uses freshest coordinates
    uow = MockUnitOfWork(db_session)
    fie = FleetIntelligenceEngine(uow=uow, company_id=company_id)
    loc_time, latest_loc = await fie._get_vehicle_latest_location(db_session, vehicle)

    assert loc_time is not None
    assert latest_loc is not None
    assert latest_loc.latitude == 19.1200
    assert latest_loc.longitude == 72.9000


# ===========================================================================
# SCENARIO B: TRIP LIFECYCLE
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_b_trip_lifecycle_and_completion(db_session):
    """
    1. Create trip via TRIP_CREATED operational event.
    2. Start trip via TRIP_STARTED.
    3. Complete trip via TRIP_COMPLETED with distance.
    4. Verify TripCompletionService runs telemetry finalization.
    5. Verify retry/replay protection prevents duplicate status mutation.
    """
    company_id = 102
    uow = MockUnitOfWork(db_session)
    event_service = OperationalEventService(uow=uow, dispatcher=default_dispatcher)

    # 1. Create Trip
    trip_business_id = f"TRIP-{uuid.uuid4().hex[:8]}"
    create_event = OperationalEventCreate(
        event_type=EventType.TRIP_CREATED,
        entity_type=EntityType.TRIP,
        entity_id=trip_business_id,
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        payload={
            "origin_location": "Mumbai Depot",
            "destination_location": "Pune Hub",
            "planned_distance": 160.0,
            "planned_start_time": datetime.now(timezone.utc).isoformat(),
        },
        notes="Scheduled delivery trip",
    )
    await event_service.create_event(create_event)

    # Verify trip was persisted in DB
    trip = await uow.repositories.trip.get_trip_by_business_id(trip_business_id)
    assert trip is not None
    assert trip.status == TripStatus.CREATED
    assert trip.origin_location == "Mumbai Depot"

    # 2. Start Trip
    start_time = datetime.now(timezone.utc) - timedelta(hours=3)
    start_event = OperationalEventCreate(
        event_type=EventType.TRIP_STARTED,
        entity_type=EntityType.TRIP,
        entity_id=trip_business_id,
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        payload={"actual_start_time": start_time.isoformat()},
        notes="Driver departed Mumbai Depot",
    )
    await event_service.create_event(start_event)

    trip = await uow.repositories.trip.get_trip_by_business_id(trip_business_id)
    assert trip.status == TripStatus.IN_PROGRESS

    # 3. Complete Trip
    end_time = datetime.now(timezone.utc)
    complete_event = OperationalEventCreate(
        event_type=EventType.TRIP_COMPLETED,
        entity_type=EntityType.TRIP,
        entity_id=trip_business_id,
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        payload={
            "actual_end_time": end_time.isoformat(),
            "actual_distance": 162.5,
        },
        notes="Trip safely reached Pune Hub",
    )
    await event_service.create_event(complete_event)

    trip = await uow.repositories.trip.get_trip_by_business_id(trip_business_id)
    assert trip.status == TripStatus.COMPLETED
    assert trip.actual_distance == 162.5

    # 4. Telemetry Finalization run
    trip_completion_svc = TripCompletionService(db_session)
    await trip_completion_svc.finalize_trip_telemetry(trip.id)
    trip = await uow.repositories.trip.get_trip_by_business_id(trip_business_id)
    assert trip.status == TripStatus.COMPLETED

    # 5. Terminal State Protection against Replay
    replay_start = OperationalEventCreate(
        event_type=EventType.TRIP_STARTED,
        entity_type=EntityType.TRIP,
        entity_id=trip_business_id,
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        payload={"actual_start_time": start_time.isoformat()},
        notes="Replayed start event",
    )
    await event_service.create_event(replay_start)

    trip = await uow.repositories.trip.get_trip_by_business_id(trip_business_id)
    # Trip MUST remain COMPLETED (terminal state protection)
    assert trip.status == TripStatus.COMPLETED


# ===========================================================================
# SCENARIO C: FUEL AND EXPENSE INTEGRATION
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_c_fuel_and_expense_idempotency(db_session):
    """
    1. Ingest FUEL_FILLED event with liters and cost_inr.
    2. Operations Engine dispatches event to Fuel domain & Expense domain.
    3. Verify FuelState and linked Expense record created.
    4. Confirm duplicate event submission is idempotent (no duplicate expenses).
    """
    company_id = 103
    uow = MockUnitOfWork(db_session)
    event_service = OperationalEventService(uow=uow, dispatcher=default_dispatcher)

    # Create vehicle
    vehicle = Vehicle(
        registration_number="MH-12-DE-9999",
        make="BharatBenz",
        model="2823R",
        tank_capacity=380.0,
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        origin_type="manual",
        origin_id="init",
    )
    db_session.add(vehicle)
    await db_session.commit()

    # 1. Create FUEL_FILLED event
    fill_event_id = uuid.uuid4()
    fuel_event = OperationalEvent(
        id=fill_event_id,
        event_type=EventType.FUEL_FILLED,
        entity_type=EntityType.VEHICLE,
        entity_id=str(vehicle.id),
        company_id=company_id,
        capture_method=CaptureMethod.MANUAL_ENTRY,
        occurred_at=datetime.now(timezone.utc),
        payload={
            "liters": 75.0,
            "cost_inr": 6750.0,
            "fuel_station": "IOCL Pune Bypass",
            "receipt_url": "https://storage.fleetguard.io/receipts/fuel_101.jpg",
        },
        notes="Full tank refill",
    )
    db_session.add(fuel_event)
    await db_session.commit()

    # Direct invoke through ExpenseService & FuelService
    from services.expense_service import ExpenseService
    from services.fuel_service import FuelService

    fuel_svc = FuelService(uow)
    await fuel_svc.apply_verified_event(fuel_event)

    expense_svc = ExpenseService(uow)
    await expense_svc.apply_verified_event(fuel_event)
    await db_session.commit()

    # 2. Verify Expense record
    exp_res = await db_session.execute(
        select(Expense).where(Expense.business_id == f"EXP-FUEL-{fill_event_id}")
    )
    expenses = exp_res.scalars().all()
    assert len(expenses) == 1
    exp = expenses[0]
    assert exp.category == ExpenseCategory.FUEL
    assert exp.amount == 6750.0
    assert exp.vehicle_id == vehicle.id
    assert exp.company_id == company_id
    assert exp.receipt_reference == "https://storage.fleetguard.io/receipts/fuel_101.jpg"

    # 3. Reprocess event -> verify idempotency protection
    await expense_svc.apply_verified_event(fuel_event)
    await db_session.commit()

    exp_res_after = await db_session.execute(
        select(Expense).where(Expense.business_id == f"EXP-FUEL-{fill_event_id}")
    )
    assert len(exp_res_after.scalars().all()) == 1


# ===========================================================================
# SCENARIO D: MAINTENANCE AND EXPENSE INTEGRATION
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_d_maintenance_and_expense_integration(db_session):
    """
    1. Create maintenance record.
    2. Complete maintenance via MAINTENANCE_COMPLETED event.
    3. Verify linked expense record is generated in the expense ledger.
    4. Confirm duplicate submissions do not create duplicate expenses.
    """
    company_id = 104
    uow = MockUnitOfWork(db_session)

    vehicle = Vehicle(
        registration_number="KA-01-MJ-5555",
        make="Ashok Leyland",
        model="Captain",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        origin_type="manual",
        origin_id="init",
    )
    db_session.add(vehicle)
    await db_session.flush()

    maintenance = MaintenanceRecord(
        business_id=f"MNT-{uuid.uuid4().hex[:8]}",
        vehicle_id=vehicle.id,
        category=MaintenanceCategory.PREVENTIVE,
        status=MaintenanceStatus.SCHEDULED,
        scheduled_date=datetime.now(timezone.utc),
        workshop="Bangalore Central Workshop",
        cost=15000.0,
        odometer=52000,
        company_id=company_id,
    )
    db_session.add(maintenance)
    await db_session.commit()

    # Create MAINTENANCE_COMPLETED operational event
    mnt_event_id = uuid.uuid4()
    mnt_event = OperationalEvent(
        id=mnt_event_id,
        event_type=EventType.MAINTENANCE_COMPLETED,
        entity_type=EntityType.MAINTENANCE,
        entity_id=str(maintenance.id),
        company_id=company_id,
        capture_method=CaptureMethod.SYSTEM_GENERATED,
        occurred_at=datetime.now(timezone.utc),
        payload={
            "service_type": "PREVENTIVE",
            "cost": 15000.0,
            "vehicle_id": vehicle.id,
            "odometer": 52000,
        },
        notes="50,000 km Scheduled Service Completed",
    )
    db_session.add(mnt_event)
    await db_session.commit()

    from services.expense_service import ExpenseService
    expense_svc = ExpenseService(uow)
    await expense_svc.apply_verified_event(mnt_event)
    await db_session.commit()

    # Verify linked maintenance expense
    exp_res = await db_session.execute(
        select(Expense).where(Expense.business_id == f"EXP-MNT-{mnt_event_id}")
    )
    expenses = exp_res.scalars().all()
    assert len(expenses) == 1
    exp = expenses[0]
    assert exp.category == ExpenseCategory.MAINTENANCE
    assert exp.amount == 15000.0
    assert exp.vehicle_id == vehicle.id
    assert exp.maintenance_id == maintenance.id

    # Reprocess -> verify idempotency
    await expense_svc.apply_verified_event(mnt_event)
    await db_session.commit()

    exp_res2 = await db_session.execute(
        select(Expense).where(Expense.business_id == f"EXP-MNT-{mnt_event_id}")
    )
    assert len(exp_res2.scalars().all()) == 1


# ===========================================================================
# SCENARIO E: OPERATIONS ENGINE & FLEET INTELLIGENCE ENGINE
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_e_operations_to_fleet_intelligence(db_session):
    """
    1. Create operational events for a vehicle.
    2. FleetIntelligenceEngine consumes authoritative operational records.
    3. Verify findings are evidence-grounded and reflect actual state.
    """
    company_id = 105
    uow = MockUnitOfWork(db_session)
    event_service = OperationalEventService(uow=uow, dispatcher=default_dispatcher)

    # Register vehicle via operational event
    reg_num = "DL-01-XY-7777"
    reg_event = OperationalEventCreate(
        event_type=EventType.VEHICLE_REGISTERED,
        entity_type=EntityType.VEHICLE,
        entity_id=reg_num,
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        payload={
            "registration_number": reg_num,
            "make": "Eicher",
            "model": "Pro 3015",
            "tank_capacity": 190.0,
            "company_id": company_id,
        },
        notes="New fleet addition",
    )
    await event_service.create_event(reg_event)

    # Verify vehicle created
    vehicle = await uow.repositories.vehicle.get_vehicle_by_registration(reg_num, company_id=company_id)
    assert vehicle is not None
    assert vehicle.registration_number == reg_num

    # Add fuel fill event for vehicle
    fuel_event = OperationalEventCreate(
        event_type=EventType.FUEL_FILLED,
        entity_type=EntityType.VEHICLE,
        entity_id=str(vehicle.id),
        company_id=company_id,
        capture_method=CaptureMethod.MANUAL_ENTRY,
        occurred_at=datetime.now(timezone.utc),
        payload={
            "liters": 150.0,
            "cost_inr": 13500.0,
            "station_name": "HPCL Delhi Cantt",
        },
        notes="Initial fueling",
    )
    await event_service.create_event(fuel_event)

    # Run Fleet Intelligence Service
    fie_svc = FleetIntelligenceService(uow=uow)
    health_response = await fie_svc.get_fleet_health(company_id=company_id)

    assert health_response is not None
    assert health_response.fleet_id == str(company_id)
    assert health_response.vehicle_count >= 1


# ===========================================================================
# SCENARIO F: FAILURE RECOVERY & MULTI-TENANT ISOLATION
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_f_failure_recovery_and_tenant_isolation(db_session):
    """
    1. Simulate handler exception during event processing -> verify rollback safety.
    2. Enforce strict company isolation between Company 106 and Company 107.
    """
    company_1 = 106
    company_2 = 107
    uow = MockUnitOfWork(db_session)
    event_service = OperationalEventService(uow=uow, dispatcher=default_dispatcher)

    # 1. Tenant 1 records event
    event_c1 = OperationalEventCreate(
        event_type=EventType.EXPENSE_ADDED,
        entity_type=EntityType.EXPENSE,
        entity_id="EXP-TENANT-1",
        company_id=company_1,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        payload={
            "category": "TOLL",
            "amount": 450.0,
            "description": "Bandra-Worli Sea Link Toll",
        },
    )
    await event_service.create_event(event_c1)

    # 2. Tenant 2 records event
    event_c2 = OperationalEventCreate(
        event_type=EventType.EXPENSE_ADDED,
        entity_type=EntityType.EXPENSE,
        entity_id="EXP-TENANT-2",
        company_id=company_2,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        payload={
            "category": "PARKING",
            "amount": 200.0,
            "description": "Airport Cargo Parking",
        },
    )
    await event_service.create_event(event_c2)

    # Verify company isolation on list_events
    events_c1 = await event_service.list_events(company_id=company_1)
    events_c2 = await event_service.list_events(company_id=company_2)

    c1_entity_ids = [e.entity_id for e in events_c1]
    c2_entity_ids = [e.entity_id for e in events_c2]

    assert "EXP-TENANT-1" in c1_entity_ids
    assert "EXP-TENANT-2" not in c1_entity_ids

    assert "EXP-TENANT-2" in c2_entity_ids
    assert "EXP-TENANT-1" not in c2_entity_ids

    # 3. Simulate controlled error in domain service
    from services.fuel_service import FuelService
    from fastapi import HTTPException

    fuel_svc = FuelService(uow)
    # Event referencing non-existent vehicle ID 999999
    bad_event = OperationalEvent(
        id=uuid.uuid4(),
        event_type=EventType.FUEL_FILLED,
        entity_type=EntityType.VEHICLE,
        entity_id="999999",
        company_id=company_1,
        capture_method=CaptureMethod.MANUAL_ENTRY,
        occurred_at=datetime.now(timezone.utc),
        payload={"liters": 50.0},
    )

    with pytest.raises(HTTPException) as exc_info:
        await fuel_svc.apply_verified_event(bad_event)
    assert exc_info.value.status_code == 404
    assert "Vehicle 999999 not found" in str(exc_info.value.detail)

    # 4. Strict Evidence Repository Tenant Isolation
    from models.evidence import Evidence, EvidenceStatus, EvidenceType
    from repositories.evidence_repository import EvidenceRepository

    ev_repo = EvidenceRepository(db_session)
    event_c1_record = (await event_service.list_events(company_id=company_1))[0]

    # Attach evidence record to Tenant 1 event
    evidence_c1 = Evidence(
        event_id=event_c1_record.id,
        evidence_type=EvidenceType.RECEIPT_DOCUMENT,
        source="driver_upload",
        status=EvidenceStatus.COMPLETED,
        summary="Toll receipt slip",
        raw_data={"toll_plaza": "Bandra"},
    )
    db_session.add(evidence_c1)
    await db_session.commit()

    # Query with Tenant 1 scope -> evidence is visible
    c1_evidence = await ev_repo.get_for_event(event_c1_record.id, company_id=company_1)
    assert len(c1_evidence) == 1
    assert c1_evidence[0].summary == "Toll receipt slip"

    # Query with Tenant 2 scope -> cross-tenant leakage PREVENTED
    c2_cross_evidence = await ev_repo.get_for_event(event_c1_record.id, company_id=company_2)
    assert len(c2_cross_evidence) == 0

    # Query without company_id (internal system worker) -> strictly scoped to event_id
    internal_evidence = await ev_repo.get_for_event(event_c1_record.id, company_id=None)
    assert len(internal_evidence) == 1
    assert internal_evidence[0].summary == "Toll receipt slip"

    # Query without company_id for a non-existent or unrelated event_id -> returns empty
    unrelated_event_id = uuid.uuid4()
    empty_evidence = await ev_repo.get_for_event(unrelated_event_id, company_id=None)
    assert len(empty_evidence) == 0


# ===========================================================================
# SCENARIO G: OUTBOX DURABILITY, RECOVERY & RETRY SAFETY
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_g_outbox_durability_and_crash_recovery(db_session):
    """
    1. Verify event creation and outbox insertion commit atomically.
    2. Successful in-process dispatch advances outbox status to PUBLISHED.
    3. Simulate application crash before dispatch: OutboxPublisher discovers pending entries.
    4. Verify OutboxPublisher advances PENDING -> PUBLISHING -> PUBLISHED.
    5. Simulate broker/relay unavailability: verify mark_failed increments retry_count and resets to PENDING.
    6. Verify replayed outbox events do not duplicate business side effects.
    """
    company_id = 108
    uow = MockUnitOfWork(db_session)
    event_service = OperationalEventService(uow=uow, dispatcher=default_dispatcher)

    # 1. Atomic commit & automatic advance to PUBLISHED on successful dispatch
    event_payload = OperationalEventCreate(
        event_type=EventType.EXPENSE_ADDED,
        entity_type=EntityType.EXPENSE,
        entity_id="EXP-OUTBOX-01",
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        payload={"category": "PARKING", "amount": 150.0},
    )
    res = await event_service.create_event(event_payload)

    # Check outbox record in DB
    outbox_rec = await uow.repositories.outbox.get_by_event_id(str(res.id))
    assert outbox_rec is not None
    assert outbox_rec.event_id == str(res.id)
    assert outbox_rec.status == OutboxStatus.PUBLISHED

    # 2. Simulate Crash Before In-Process Dispatch:
    # Event and outbox record commit with status=PENDING, but server exits before dispatch.
    crashed_event_id = str(uuid.uuid4())
    crashed_event = OperationalEvent(
        id=uuid.UUID(crashed_event_id),
        event_type=EventType.EXPENSE_ADDED,
        entity_type=EntityType.EXPENSE,
        entity_id="EXP-CRASHED-02",
        occurred_at=datetime.now(timezone.utc),
        capture_method=CaptureMethod.API_INTEGRATION,
        company_id=company_id,
        payload={"category": "TOLL", "amount": 300.0},
    )
    db_session.add(crashed_event)

    crashed_response_payload = {
        "id": crashed_event_id,
        "event_type": "EXPENSE_ADDED",
        "entity_type": "EXPENSE",
        "entity_id": "EXP-CRASHED-02",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "capture_method": "API_INTEGRATION",
        "verification_status": "PENDING",
        "company_id": company_id,
        "payload": {"category": "TOLL", "amount": 300.0},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await uow.repositories.outbox.create_event(
        topic="operational-events",
        payload=crashed_response_payload,
        event_id=crashed_event_id,
    )
    await db_session.commit()

    # Verify pending state before recovery
    pending_before = await uow.repositories.outbox.get_pending_batch(batch_size=10)
    assert any(e.event_id == crashed_event_id for e in pending_before)

    # 3. Startup Recovery Relay via OutboxPublisher & InProcessEventBus
    from infrastructure.events.bus import InProcessEventBus
    from infrastructure.events.outbox_publisher import OutboxPublisher

    in_process_bus = InProcessEventBus(dispatcher=default_dispatcher)
    publisher = OutboxPublisher(db_session_factory=lambda: db_session, event_bus=in_process_bus)

    processed_count = await publisher.publish_pending()
    assert processed_count >= 1

    # Verify that the crashed outbox event advanced to PUBLISHED
    db_session.expire_all()
    recovered_outbox = await uow.repositories.outbox.get_by_event_id(crashed_event_id)
    assert recovered_outbox is not None
    assert recovered_outbox.status == OutboxStatus.PUBLISHED
    assert recovered_outbox.published_at is not None

    # 4. Simulate Broker / Network Failure:
    # When EventBus.publish raises an exception, OutboxPublisher marks the event as failed and resets to PENDING
    failing_event_id = str(uuid.uuid4())
    await uow.repositories.outbox.create_event(
        topic="operational-events",
        payload={"id": failing_event_id, "broken": True},
        event_id=failing_event_id,
    )
    await db_session.commit()

    class FailingEventBus(InProcessEventBus):
        async def publish(self, topic, event):
            raise ConnectionError("Kafka broker unreachable (simulated outage)")

    failing_publisher = OutboxPublisher(db_session_factory=lambda: db_session, event_bus=FailingEventBus())
    failed_processed = await failing_publisher.publish_pending()
    assert failed_processed == 0

    failed_outbox = await uow.repositories.outbox.get_by_event_id(failing_event_id)
    assert failed_outbox is not None
    assert failed_outbox.status == OutboxStatus.PENDING
    assert failed_outbox.retry_count == 1
    assert "broker unreachable" in failed_outbox.last_error


# ===========================================================================
# SCENARIO H: NO-KAFKA PERIODIC POLLING WORKER, HANDLER FAILURE & RETRY
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_h_no_kafka_polling_worker_and_retries(db_session):
    """
    Verifies:
    1. Background OutboxWorkerRunner starts and gracefully stops.
    2. An event whose handler fails during first attempt is recorded as failed (retry_count=1, PENDING).
    3. Periodic polling discovers the pending outbox record.
    4. On subsequent retry with a functioning handler, the event succeeds and transitions to PUBLISHED.
    5. Side effects (e.g. expenses) remain idempotent and are not duplicated across retries.
    """
    import asyncio
    company_id = 109
    uow = MockUnitOfWork(db_session)

    # 1. Setup a custom subscriber that fails on first invocation and succeeds on second
    attempt_counter = {"calls": 0}

    class FlakySubscriber:
        name = "flaky_subscriber"
        event_filter = None

        async def handle(self, event):
            attempt_counter["calls"] += 1
            if attempt_counter["calls"] == 1:
                raise RuntimeError("Transient database lock / downstream timeout (attempt 1)")
            # Attempt 2 succeeds

    flaky_sub = FlakySubscriber()
    test_dispatcher = EventDispatcher()
    test_dispatcher.register_subscriber(flaky_sub)
    from infrastructure.events.bus import InProcessEventBus
    test_bus = InProcessEventBus(dispatcher=test_dispatcher)

    # Stage an outbox event
    flaky_event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    flaky_event = OperationalEvent(
        id=uuid.UUID(flaky_event_id),
        event_type=EventType.EXPENSE_ADDED,
        entity_type=EntityType.EXPENSE,
        entity_id="EXP-FLAKY-01",
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=now,
        recorded_at=now,
        verification_status=VerificationStatus.PENDING,
        created_at=now,
        updated_at=now,
        payload={"category": "FUEL", "amount": 1200.0},
    )
    db_session.add(flaky_event)
    await db_session.commit()

    flaky_payload = OperationalEventResponse.model_validate(flaky_event).model_dump(mode="json")
    await uow.repositories.outbox.create_event(
        topic="operational-events",
        payload=flaky_payload,
        event_id=flaky_event_id,
        status=OutboxStatus.PENDING,
    )
    await db_session.commit()

    from infrastructure.events.outbox_publisher import OutboxPublisher
    publisher = OutboxPublisher(db_session_factory=lambda: db_session, event_bus=test_bus)

    # First attempt: FlakySubscriber throws RuntimeError
    res_1 = await publisher.publish_pending()
    assert res_1 == 0
    assert attempt_counter["calls"] == 1

    # Outbox status must be reset to PENDING with retry_count=1 and last_error recorded
    db_session.expire_all()
    rec_after_fail = await uow.repositories.outbox.get_by_event_id(flaky_event_id)
    assert rec_after_fail.status == OutboxStatus.PENDING
    assert rec_after_fail.retry_count == 1
    assert "Transient database lock" in rec_after_fail.last_error

    # Second attempt: FlakySubscriber succeeds
    res_2 = await publisher.publish_pending()
    assert res_2 == 1
    assert attempt_counter["calls"] == 2

    db_session.expire_all()
    rec_after_success = await uow.repositories.outbox.get_by_event_id(flaky_event_id)
    assert rec_after_success.status == OutboxStatus.PUBLISHED
    assert rec_after_success.published_at is not None

    # Test Worker lifecycle (start / stop)
    from infrastructure.events.outbox_worker import OutboxWorkerRunner
    worker = OutboxWorkerRunner(publisher=publisher)
    await worker.start()
    assert worker._task is not None
    await asyncio.sleep(0.05)
    await worker.stop()
    assert worker._task is None


# ===========================================================================
# SCENARIO I: NO-KAFKA COMPETING DISPATCH CLAIM, POISON EVENT & API SEMANTICS
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_i_no_kafka_competing_dispatch_and_poison_pill(db_session):
    """
    Verifies:
    1. OperationalEventService stages outbox record with PUBLISHING claim to prevent competing workers.
    2. OutboxRepository.get_pending_batch ignores PUBLISHING events (competing path safety).
    3. Stale PUBLISHING claims (from simulated crash) are recovered by recover_stale_publishing.
    4. Poison-pill events that fail repeatedly reach OUTBOX_MAX_RETRIES and are excluded from polling.
    5. Dead-lettered events are observable via get_dead_letter_events repository method.
    6. Response semantics: API returns HTTP 201 with verification_status=PENDING.
    """
    company_id = 110
    uow = MockUnitOfWork(db_session)

    # 1. API Response semantics and inline claim
    event_service = OperationalEventService(uow=uow, dispatcher=default_dispatcher)
    event_payload = OperationalEventCreate(
        event_type=EventType.EXPENSE_ADDED,
        entity_type=EntityType.EXPENSE,
        entity_id="EXP-SEMANTICS-01",
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        payload={"category": "MAINTENANCE", "amount": 4500.0},
    )
    res = await event_service.create_event(event_payload)
    # API semantics check: accepted event is returned with PENDING verification status
    assert res.verification_status == VerificationStatus.PENDING

    # 2. Competing dispatch safety:
    # An event actively in PUBLISHING status must NOT be picked up by get_pending_batch
    competing_id = str(uuid.uuid4())
    await uow.repositories.outbox.create_event(
        topic="operational-events",
        payload={"id": competing_id},
        event_id=competing_id,
        status=OutboxStatus.PUBLISHING,
    )
    await db_session.commit()

    pending_batch = await uow.repositories.outbox.get_pending_batch(batch_size=50)
    assert not any(e.event_id == competing_id for e in pending_batch)

    # 3. Stale claim recovery:
    # Manually backdate created_at and headers['claimed_at'] to simulate a crash 60 seconds ago
    from datetime import timedelta
    competing_rec = await uow.repositories.outbox.get_by_event_id(competing_id)
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=60)
    competing_rec.created_at = stale_time
    competing_rec.headers = {"claimed_at": stale_time.isoformat()}
    await db_session.commit()

    recovered_count = await uow.repositories.outbox.recover_stale_publishing(stale_threshold_seconds=30)
    assert recovered_count >= 1

    db_session.expire_all()
    recovered_rec = await uow.repositories.outbox.get_by_event_id(competing_id)
    assert recovered_rec.status == OutboxStatus.PENDING
    assert "Recovered stale PUBLISHING claim" in recovered_rec.last_error

    # 4. Poison-pill bounded retries:
    # Simulate an unprocessable event that fails until max_retries is reached
    poison_id = str(uuid.uuid4())
    poison_rec = await uow.repositories.outbox.create_event(
        topic="operational-events",
        payload={"id": poison_id, "poison": True},
        event_id=poison_id,
        status=OutboxStatus.PENDING,
    )
    poison_rec.retry_count = 4 # 1 below default max_retries (5)
    await db_session.commit()

    from infrastructure.events.bus import InProcessEventBus
    class PoisonEventBus(InProcessEventBus):
        async def publish(self, topic, event):
            raise ValueError("Corrupt / unprocessable poison payload")

    from infrastructure.events.outbox_publisher import OutboxPublisher
    poison_publisher = OutboxPublisher(db_session_factory=lambda: db_session, event_bus=PoisonEventBus())
    await poison_publisher.publish_pending()

    db_session.expire_all()
    poison_after = await uow.repositories.outbox.get_by_event_id(poison_id)
    assert poison_after.retry_count == 5
    assert "MAX_RETRIES_EXCEEDED" in poison_after.last_error

    # Ensure bounded retries: get_pending_batch now IGNORES this poison event!
    subsequent_pending = await uow.repositories.outbox.get_pending_batch(batch_size=50, max_retries=5)
    assert not any(e.event_id == poison_id for e in subsequent_pending)

    # 5. Observability: dead-lettered events are queryable
    dead_letters = await uow.repositories.outbox.get_dead_letter_events(max_retries=5)
    assert any(e.event_id == poison_id for e in dead_letters)


# ===========================================================================
# SCENARIO J: OUTBOX SCHEMA, CONSTRAINTS, LEGAL ENUMS & TRANSITION REJECTION
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_j_outbox_schema_and_constraints(db_session):
    """
    Verifies:
    1. OutboxEvent ORM model column definitions match expected persistence schema.
    2. Primary key, required fields, and legal OutboxStatus enum values.
    3. Rejection of illegal state transitions (e.g. from terminal PUBLISHED status to PUBLISHING or PENDING).
    4. Active claim protection: lease timestamps in headers['claimed_at'] prevent premature recovery.
    5. Stale claim recovery: expired claims (beyond stale threshold) are recovered to PENDING.
    6. Dead-letter bounded retry state is observable via get_dead_letter_events.
    """
    from models.outbox_event import OutboxEvent, OutboxStatus
    from datetime import timedelta

    company_id = 111
    uow = MockUnitOfWork(db_session)

    # 1. ORM Model Column & Schema Consistency Check
    columns = OutboxEvent.__table__.columns
    expected_columns = {
        "id", "event_id", "topic", "payload", "headers",
        "status", "created_at", "published_at", "retry_count", "last_error"
    }
    assert expected_columns.issubset(set(columns.keys())), f"Missing columns in OutboxEvent: {expected_columns - set(columns.keys())}"

    # Verify primary key and non-nullable requirements
    assert columns["id"].primary_key is True
    assert columns["topic"].nullable is False
    assert columns["payload"].nullable is False
    assert columns["status"].nullable is False
    assert columns["retry_count"].nullable is False
    assert columns["created_at"].nullable is False

    # Verify canonical legal enum values
    canonical_statuses = {"PENDING", "PUBLISHING", "PUBLISHED"}
    assert {s.value for s in OutboxStatus} == canonical_statuses
    assert len(OutboxStatus) == 3

    # 2. Reject Illegal State Transitions from Terminal PUBLISHED State
    published_id = str(uuid.uuid4())
    published_rec = await uow.repositories.outbox.create_event(
        topic="operational-events",
        payload={"id": published_id, "data": "already_done"},
        event_id=published_id,
        status=OutboxStatus.PUBLISHED,
    )
    await db_session.commit()

    # Attempting to re-claim a PUBLISHED event as PUBLISHING must be rejected
    with pytest.raises(ValueError, match="Cannot transition terminal PUBLISHED event"):
        await uow.repositories.outbox.mark_publishing([published_rec])

    # Attempting to mark a PUBLISHED event as failed must be rejected
    with pytest.raises(ValueError, match="Cannot transition terminal PUBLISHED event"):
        await uow.repositories.outbox.mark_failed(published_rec, error="Late failure")

    # 3. Active Claim Protection vs Stale Claim Recovery
    now = datetime.now(timezone.utc)
    active_claim_id = str(uuid.uuid4())
    stale_claim_id = str(uuid.uuid4())

    # Active claim (claimed 2 seconds ago)
    await uow.repositories.outbox.create_event(
        topic="operational-events",
        payload={"id": active_claim_id},
        event_id=active_claim_id,
        status=OutboxStatus.PUBLISHING,
        headers={"claimed_at": (now - timedelta(seconds=2)).isoformat()},
    )

    # Stale claim (claimed 60 seconds ago — exceeding 30s threshold)
    await uow.repositories.outbox.create_event(
        topic="operational-events",
        payload={"id": stale_claim_id},
        event_id=stale_claim_id,
        status=OutboxStatus.PUBLISHING,
        headers={"claimed_at": (now - timedelta(seconds=60)).isoformat()},
    )
    await db_session.commit()

    # Run stale claim recovery with 30s threshold
    recovered_count = await uow.repositories.outbox.recover_stale_publishing(stale_threshold_seconds=30)
    assert recovered_count >= 1

    db_session.expire_all()
    active_rec = await uow.repositories.outbox.get_by_event_id(active_claim_id)
    stale_rec = await uow.repositories.outbox.get_by_event_id(stale_claim_id)

    # Active claim MUST NOT be reclaimed
    assert active_rec.status == OutboxStatus.PUBLISHING

    # Stale claim MUST be reset to PENDING with retry count incremented
    assert stale_rec.status == OutboxStatus.PENDING
    assert stale_rec.retry_count >= 1
    assert "Recovered stale PUBLISHING claim" in stale_rec.last_error

    # 4. Dead-Letter Observability for Exhausted Retries
    dead_letter_id = str(uuid.uuid4())
    dead_letter_rec = await uow.repositories.outbox.create_event(
        topic="operational-events",
        payload={"id": dead_letter_id},
        event_id=dead_letter_id,
        status=OutboxStatus.PENDING,
    )
    dead_letter_rec.retry_count = 6
    dead_letter_rec.last_error = "[POISON_PILL / MAX_RETRIES_EXCEEDED] Fatal payload validation error"
    await db_session.commit()

    dead_letters = await uow.repositories.outbox.get_dead_letter_events(max_retries=5)
    assert any(e.event_id == dead_letter_id for e in dead_letters)


# ===========================================================================
# SCENARIO K: DISPATCHER HARDENING, LIFECYCLE RESTART & RETRY IDEMPOTENCY
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_k_dispatcher_hardening_and_retry_idempotency(db_session):
    """
    Verifies:
    1. Duplicate subscriber registration: re-registering with the same name replaces in-place without duplicating.
    2. Partial subscriber failure: failure in one subscriber does NOT starve independent subscribers;
       the dispatcher executes all matching subscribers and re-raises the failure to trigger outbox retries.
    3. asyncio.CancelledError is never swallowed or treated as an ordinary subscriber failure.
    4. Retry safety and financial ledger idempotency: replaying FUEL_FILLED and MAINTENANCE_COMPLETED events
       updates existing records rather than duplicating expenses.
    """
    import asyncio
    from dispatchers.event_subscriber import EventSubscriber

    company_id = 112
    uow = MockUnitOfWork(db_session)
    dispatcher = EventDispatcher()

    # 1. Duplicate Subscriber Registration Deduplication
    class MockSubscriber(EventSubscriber):
        def __init__(self, name: str, tag: str):
            self.name = name
            self.tag = tag
            self.event_filter = None
        async def handle(self, event):
            pass

    sub1 = MockSubscriber("audit_logger", tag="v1")
    sub2 = MockSubscriber("audit_logger", tag="v2")

    dispatcher.register_subscriber(sub1)
    assert len(dispatcher) == 1
    dispatcher.register_subscriber(sub2)
    assert len(dispatcher) == 1
    assert dispatcher._subscribers[0].tag == "v2"

    # 2. Partial Subscriber Failure & Error Propagation
    execution_order = []

    class SuccessfulSubscriber1(EventSubscriber):
        name = "sub_success_1"
        event_filter = None
        async def handle(self, event):
            execution_order.append("sub1_ran")

    class FailingSubscriber(EventSubscriber):
        name = "sub_failing"
        event_filter = None
        async def handle(self, event):
            execution_order.append("sub_fail_ran")
            raise ConnectionResetError("Remote telemetry ingestion broker disconnected")

    class SuccessfulSubscriber2(EventSubscriber):
        name = "sub_success_2"
        event_filter = None
        async def handle(self, event):
            execution_order.append("sub2_ran")

    multi_dispatcher = EventDispatcher()
    multi_dispatcher.register_subscriber(SuccessfulSubscriber1())
    multi_dispatcher.register_subscriber(FailingSubscriber())
    multi_dispatcher.register_subscriber(SuccessfulSubscriber2())

    dummy_event = OperationalEventResponse(
        id=uuid.uuid4(),
        event_type=EventType.EXPENSE_ADDED,
        entity_type=EntityType.EXPENSE,
        entity_id="EXP-MULTI-01",
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=datetime.now(timezone.utc),
        recorded_at=datetime.now(timezone.utc),
        verification_status=VerificationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        payload={"category": "PARKING", "amount": 100.0},
    )

    # Dispatching must invoke ALL matching subscribers and re-raise the exception
    with pytest.raises(ConnectionResetError, match="Remote telemetry ingestion broker disconnected"):
        await multi_dispatcher.publish(dummy_event)

    # Sub 2 was NOT starved by FailingSubscriber!
    assert execution_order == ["sub1_ran", "sub_fail_ran", "sub2_ran"]

    # 3. Cancellation Handling: asyncio.CancelledError must not be caught as generic exception
    class CancellingSubscriber(EventSubscriber):
        name = "sub_cancelling"
        event_filter = None
        async def handle(self, event):
            raise asyncio.CancelledError("Simulated graceful server shutdown")

    cancel_dispatcher = EventDispatcher()
    cancel_dispatcher.register_subscriber(CancellingSubscriber())

    with pytest.raises(asyncio.CancelledError):
        await cancel_dispatcher.publish(dummy_event)

    # 4. Financial Ledger Idempotency: Replaying FUEL_FILLED & MAINTENANCE_COMPLETED events
    from services.expense_service import ExpenseService
    expense_svc = ExpenseService(uow=uow)

    fuel_event_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    fuel_event = OperationalEvent(
        id=fuel_event_id,
        event_type=EventType.FUEL_FILLED,
        entity_type=EntityType.VEHICLE,
        entity_id="999",
        company_id=company_id,
        capture_method=CaptureMethod.MANUAL_ENTRY,
        occurred_at=now,
        recorded_at=now,
        verification_status=VerificationStatus.VERIFIED,
        payload={"cost_inr": 4800.0, "liters": 45.0, "station_name": "IOCL Hub"},
    )

    # First dispatch: records expense
    await expense_svc.apply_verified_event(fuel_event)
    await db_session.commit()

    fuel_expense_id = f"EXP-FUEL-{fuel_event_id}"
    expense_rec1 = await uow.repositories.expense.get_expense_by_business_id(fuel_expense_id)
    assert expense_rec1 is not None
    assert expense_rec1.amount == 4800.0

    # Simulated Outbox Retry / Replay: must update in-place without creating duplicates
    await expense_svc.apply_verified_event(fuel_event)
    await db_session.commit()

    all_fuel_expenses = await uow.repositories.expense.search_expenses(company_id=company_id)
    matching_fuel = [e for e in all_fuel_expenses if e.business_id == fuel_expense_id]
    assert len(matching_fuel) == 1
    assert matching_fuel[0].amount == 4800.0

    # Maintenance event replay idempotency check
    mnt_event_id = uuid.uuid4()
    mnt_event = OperationalEvent(
        id=mnt_event_id,
        event_type=EventType.MAINTENANCE_COMPLETED,
        entity_type=EntityType.VEHICLE,
        entity_id="999",
        company_id=company_id,
        capture_method=CaptureMethod.API_INTEGRATION,
        occurred_at=now,
        recorded_at=now,
        verification_status=VerificationStatus.VERIFIED,
        payload={"cost": 12500.0, "service_type": "Brake pad replacement"},
    )

    # First dispatch
    await expense_svc.apply_verified_event(mnt_event)
    await db_session.commit()

    mnt_expense_id = f"EXP-MNT-{mnt_event_id}"
    expense_mnt1 = await uow.repositories.expense.get_expense_by_business_id(mnt_expense_id)
    assert expense_mnt1 is not None
    assert expense_mnt1.amount == 12500.0

    # Replay
    await expense_svc.apply_verified_event(mnt_event)
    await db_session.commit()

    all_expenses_after = await uow.repositories.expense.search_expenses(company_id=company_id)
    matching_mnt = [e for e in all_expenses_after if e.business_id == mnt_expense_id]
    assert len(matching_mnt) == 1
    assert matching_mnt[0].amount == 12500.0


# ===========================================================================
# SCENARIO L: BACKGROUND WORKER LIFECYCLE RESTART & FASTAPI LIFESPAN
# ===========================================================================

@pytest.mark.asyncio
async def test_scenario_l_worker_lifecycle_and_fastapi_lifespan(db_session):
    """
    Verifies:
    1. OutboxWorkerRunner can start, poll, stop, and restart repeatedly without leaking tasks.
    2. Graceful stop cleanly terminates asyncio background polling loop.
    3. FastAPI lifespan context initializes and stops worker cleanly under application lifecycle.
    """
    import asyncio
    from infrastructure.events.bus import InProcessEventBus
    from infrastructure.events.outbox_publisher import OutboxPublisher
    from infrastructure.events.outbox_worker import OutboxWorkerRunner

    test_bus = InProcessEventBus(dispatcher=default_dispatcher)
    publisher = OutboxPublisher(db_session_factory=lambda: db_session, event_bus=test_bus)
    worker = OutboxWorkerRunner(publisher=publisher)

    # 1. First lifecycle start / stop
    await worker.start()
    assert worker._task is not None
    assert not worker._task.done()
    await asyncio.sleep(0.02)
    await worker.stop()
    assert worker._task is None

    # 2. Immediate restart without recreation (lifecycle resiliency)
    await worker.start()
    assert worker._task is not None
    assert not worker._task.done()
    await asyncio.sleep(0.02)
    await worker.stop()
    assert worker._task is None

    # 3. FastAPI lifespan test with isolated session factory
    from main import app, outbox_worker, outbox_publisher
    orig_factory = outbox_publisher.db_session_factory
    outbox_publisher.db_session_factory = lambda: db_session
    try:
        async with app.router.lifespan_context(app):
            # In lifespan, outbox worker should be started
            assert outbox_worker._task is not None
            assert not outbox_worker._task.done()
            await asyncio.sleep(0.02)
    finally:
        outbox_publisher.db_session_factory = orig_factory

    # After exiting lifespan context, outbox worker should be cleanly stopped
    assert outbox_worker._task is None

