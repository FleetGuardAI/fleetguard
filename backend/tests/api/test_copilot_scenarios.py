"""
End-to-End Scenario Verification for Fleetguard AI Co-Pilot
Validates all 9 user conversation scenarios against real database state and tool execution.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus
from models.trip_domain import Trip, TripStatus
from models.location_tracking import DriverLocation, LocationSource
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus
from services.copilot_tools import CopilotToolExecutor
from services.copilot_proposal import TripProposalManager
from services.copilot_service import CopilotService
from schemas.copilot import CopilotChatRequest
from infrastructure.llm.provider import LLMMessage, LLMResponse


@pytest.fixture(autouse=True)
def reset_proposals():
    TripProposalManager.reset()
    yield
    TripProposalManager.reset()


@pytest.mark.asyncio
async def test_all_nine_realistic_conversations(db_session, monkeypatch):
    """
    Verifies all 9 user conversation flows defined in Section 5 of the audit:
    1. 'How many trucks are active?'
    2. 'Tell me the locations of both trucks.'
    3. 'Where is Truck 02, and when was its location last updated?'
    4. 'Which drivers are available?'
    5. 'Show my ongoing trips.'
    6. 'Schedule a trip for Truck 02 tomorrow.' (missing details & validation)
    7. 'Assign the available driver to this trip.' (proposal -> confirmation -> DB verification)
    8. 'Show me the latest fuel expenses.'
    9. 'What is wrong with this vehicle?' (insufficient records handled safely without hallucination)
    """
    company_id = 1001
    now = datetime.now(timezone.utc)

    # 1. Setup Fleet: 2 Vehicles (Truck 01 = Active, Truck 02 = Maintenance)
    v1 = Vehicle(registration_number="MH12AA1001", make="Tata", model="Prima", status=VehicleStatus.ACTIVE, company_id=company_id)
    v2 = Vehicle(registration_number="MH12BB2002", make="BharatBenz", model="2823R", status=VehicleStatus.MAINTENANCE, company_id=company_id)
    db_session.add_all([v1, v2])
    await db_session.flush()

    # 2. Setup Drivers: Driver 1 (Available), Driver 2 (Busy on Trip)
    d1 = Driver(name="Joginder Singh", phone_number="+919800000001", status=DriverStatus.ACTIVE, company_id=company_id)
    d2 = Driver(name="Suraj Verma", phone_number="+919800000002", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add_all([d1, d2])
    await db_session.flush()

    # 3. Setup Telemetry: Truck 01 has fresh GPS, Truck 02 has stale GPS (2 hours ago)
    loc1 = DriverLocation(
        driver_id=d1.id,
        company_id=company_id,
        latitude=19.0760,
        longitude=72.8777,
        timestamp=now - timedelta(minutes=5),
        source=LocationSource.PHONE_GPS,
        speed=15.0
    )
    v1.assigned_driver_id = d1.id

    loc2 = DriverLocation(
        driver_id=d2.id,
        company_id=company_id,
        latitude=28.7041,
        longitude=77.1025,
        timestamp=now - timedelta(hours=2),
        source=LocationSource.HARDWARE_GPS,
        speed=0.0
    )
    v2.assigned_driver_id = d2.id
    db_session.add_all([loc1, loc2])

    # 4. Setup Ongoing Trip: Driver 2 is busy on an ongoing trip
    ongoing_trip = Trip(
        trip_id="TRP-ACTIVE-888",
        status=TripStatus.IN_PROGRESS,
        origin_location="Delhi",
        destination_location="Jaipur",
        vehicle_id=v1.id,
        driver_id=d2.id,
        company_id=company_id
    )
    db_session.add(ongoing_trip)

    # 5. Setup Fuel Expenses
    fuel_exp = Expense(
        business_id="EXP-FUEL-1001",
        category=ExpenseCategory.FUEL,
        amount=6500.0,
        currency="INR",
        status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1),
        description="Diesel 60L refill",
        company_id=company_id,
        origin_id="EVT-FUEL-01"
    )
    db_session.add(fuel_exp)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_admin")

    # --------------------------------------------------------------------------
    # Scenario 1: "How many trucks are active?"
    # --------------------------------------------------------------------------
    summary_raw = await executor.execute("get_fleet_summary", {})
    summary = json.loads(summary_raw)
    assert summary["total_vehicles"] == 2
    assert summary["active_vehicles"] == 1
    assert summary["maintenance_vehicles"] == 1

    # --------------------------------------------------------------------------
    # Scenario 2: "Tell me the locations of both trucks."
    # --------------------------------------------------------------------------
    both_locs_raw = await executor.execute("get_vehicle_location", {"query": "both"})
    both_locs = json.loads(both_locs_raw)
    assert both_locs["total_count"] == 2
    loc_items = {l["registration_number"]: l for l in both_locs["locations"]}
    assert loc_items["MH12AA1001"]["freshness"] == "FRESH"
    assert loc_items["MH12BB2002"]["freshness"] == "STALE"

    # --------------------------------------------------------------------------
    # Scenario 3: "Where is Truck 02, and when was its location last updated?"
    # --------------------------------------------------------------------------
    truck2_loc_raw = await executor.execute("get_vehicle_location", {"query": "Truck 02"})
    truck2_loc = json.loads(truck2_loc_raw)
    assert truck2_loc["registration_number"] == "MH12BB2002"
    assert truck2_loc["has_location"] is True
    assert truck2_loc["freshness"] == "STALE"
    assert truck2_loc["timestamp"] is not None
    assert "28.7041" in truck2_loc["address"]

    # --------------------------------------------------------------------------
    # Scenario 4: "Which drivers are available?"
    # --------------------------------------------------------------------------
    drivers_raw = await executor.execute("list_drivers", {})
    drivers_data = json.loads(drivers_raw)
    assert drivers_data["available_count"] == 1
    assert drivers_data["busy_count"] == 1
    driver_lookup = {d["name"]: d for d in drivers_data["drivers"]}
    assert driver_lookup["Joginder Singh"]["is_available"] is True
    assert driver_lookup["Joginder Singh"]["availability_status"] == "AVAILABLE"
    assert driver_lookup["Suraj Verma"]["is_available"] is False
    assert driver_lookup["Suraj Verma"]["availability_status"] == "BUSY_ON_TRIP"

    # --------------------------------------------------------------------------
    # Scenario 5: "Show my ongoing trips."
    # --------------------------------------------------------------------------
    trips_raw = await executor.execute("list_trips", {"status": "IN_PROGRESS"})
    trips_data = json.loads(trips_raw)
    assert trips_data["total_count"] == 1
    assert trips_data["trips"][0]["business_id"] == "TRP-ACTIVE-888"
    assert trips_data["trips"][0]["status"] == "IN_PROGRESS"

    # --------------------------------------------------------------------------
    # Scenario 6: "Schedule a trip for Truck 02 tomorrow."
    # Missing origin and destination -> must return MISSING_INFORMATION
    # --------------------------------------------------------------------------
    incomplete_raw = await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "Truck 02",
        "planned_start_time": "2026-10-28T10:00:00"
    })
    incomplete = json.loads(incomplete_raw)
    assert incomplete["status"] == "MISSING_INFORMATION"

    # When vehicle is in MAINTENANCE, attempting to propose trip must enforce business constraint
    maint_attempt_raw = await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "Truck 02",
        "origin": "Mumbai",
        "destination": "Goa",
        "planned_start_time": "2026-10-28T10:00:00"
    })
    maint_attempt = json.loads(maint_attempt_raw)
    assert maint_attempt["status"] == "CONSTRAINT_VIOLATION"
    assert "MAINTENANCE" in maint_attempt["error"]

    # --------------------------------------------------------------------------
    # Scenario 7: "Assign the available driver to this trip."
    # We schedule for active vehicle (v1) with driver_query="available"
    # Note: v1 is currently on ongoing_trip, so it should report VEHICLE_BUSY!
    # --------------------------------------------------------------------------
    busy_v_raw = await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12AA1001",
        "driver_query": "available",
        "origin": "Mumbai",
        "destination": "Pune",
        "planned_start_time": "2026-10-28T10:00:00"
    })
    busy_v = json.loads(busy_v_raw)
    assert busy_v["status"] == "VEHICLE_BUSY"

    # Now let's complete the ongoing trip so v1 is free, and test successful proposal & confirmation
    ongoing_trip.status = TripStatus.COMPLETED
    await db_session.commit()

    prop_raw = await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12AA1001",
        "driver_query": "available",
        "origin": "Mumbai",
        "destination": "Pune",
        "planned_start_time": "2026-10-28T10:00:00",
        "planned_distance_km": 150.0,
        "revenue": 12000.0
    })
    prop = json.loads(prop_raw)
    assert prop["status"] == "PROPOSAL_READY"
    assert prop["summary"]["driver"] == "Joginder Singh"  # Auto-selected available driver
    proposal_id = prop["proposal_id"]

    # Verify trip does NOT exist in DB prior to confirmation
    db_trips_before = (await db_session.execute(select(Trip).where(Trip.origin_type == "copilot_ai"))).scalars().all()
    assert len(db_trips_before) == 0

    # Explicit server confirmation
    confirm_raw = await executor.execute("confirm_trip_execution", {"proposal_id": proposal_id})
    confirm = json.loads(confirm_raw)
    assert confirm["status"] == "SUCCESS"
    assert confirm["verified"] is True
    new_trip_id = confirm["trip_id"]

    # Verify trip record exists in database after confirmation
    db_trip = await db_session.get(Trip, new_trip_id)
    assert db_trip is not None
    assert db_trip.status == TripStatus.CREATED
    assert db_trip.origin_location == "Mumbai"
    assert db_trip.destination_location == "Pune"
    assert db_trip.driver_id == d1.id

    # --------------------------------------------------------------------------
    # Scenario 8: "Show me the latest fuel expenses."
    # --------------------------------------------------------------------------
    fuel_res_raw = await executor.execute("list_expenses", {"category": "FUEL"})
    fuel_res = json.loads(fuel_res_raw)
    assert fuel_res["total_count"] == 1
    assert fuel_res["total_amount"] == 6500.0
    assert fuel_res["expenses"][0]["business_id"] == "EXP-FUEL-1001"
    assert fuel_res["expenses"][0]["description"] == "Diesel 60L refill"

    # --------------------------------------------------------------------------
    # Scenario 9: "What is wrong with this vehicle?"
    # Vehicle 2 is in MAINTENANCE, but has NO work orders or tickets logged.
    # Must report records_sufficient = False and explain that records are insufficient.
    # --------------------------------------------------------------------------
    diag_raw = await executor.execute("get_vehicle_details", {"query": "Truck 02"})
    diag = json.loads(diag_raw)
    assessment = diag["diagnostic_assessment"]
    assert assessment["status"] == "MAINTENANCE"
    assert assessment["records_sufficient"] is False
    assert len(assessment["logged_issues"]) == 0
    assert "Available records are insufficient" in assessment["diagnostic_notes"]
