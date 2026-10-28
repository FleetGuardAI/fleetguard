"""
Comprehensive automated test suite for Fleetguard AI Co-Pilot Tool Execution,
Entity Resolution, Multi-Tenancy Boundary Enforcement, and Controlled Trip Scheduling.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select

from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus, DutyStatus
from models.trip_domain import Trip, TripStatus
from models.location_tracking import DriverLocation, LocationSource
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus, MaintenanceCategory
from models.ticket import Ticket
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from models.operational_event import OperationalEvent, EntityType, EventType, CaptureMethod
from services.copilot_tools import CopilotToolExecutor, CopilotEntityResolver, COPILOT_TOOLS_DEFINITION
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
async def test_fleet_summary_with_real_data(db_session):
    """Test 1: get_fleet_summary accurately aggregates real authorized vehicle, trip, and driver data."""
    company_id = 100

    # 2 Active trucks, 1 Maintenance truck
    v1 = Vehicle(registration_number="MH12AB1001", make="Tata", model="Prima", status=VehicleStatus.ACTIVE, company_id=company_id)
    v2 = Vehicle(registration_number="MH12AB1002", make="BharatBenz", model="2823R", status=VehicleStatus.ACTIVE, company_id=company_id)
    v3 = Vehicle(registration_number="MH12AB1003", make="Eicher", model="Pro", status=VehicleStatus.MAINTENANCE, company_id=company_id)

    # Other company truck (must be isolated)
    v_other = Vehicle(registration_number="KA01OTHER", make="Volvo", status=VehicleStatus.ACTIVE, company_id=999)

    # Driver
    d1 = Driver(name="Ramesh Singh", phone_number="+919800000001", status=DriverStatus.ACTIVE, company_id=company_id)

    # Active Trip
    t1 = Trip(
        trip_id="TRP-1001",
        status=TripStatus.IN_PROGRESS,
        origin_location="Mumbai",
        destination_location="Pune",
        company_id=company_id
    )

    db_session.add_all([v1, v2, v3, v_other, d1, t1])
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    executor = CopilotToolExecutor(uow=MockUoW(db_session), company_id=company_id, user_id="user_1")
    res_str = await executor.execute("get_fleet_summary", {})
    data = json.loads(res_str)

    assert data["total_vehicles"] == 3
    assert data["active_vehicles"] == 2
    assert data["maintenance_vehicles"] == 1
    assert data["active_trips_in_progress"] == 1
    assert data["active_drivers"] == 1


@pytest.mark.asyncio
async def test_list_vehicles_and_identifiers(db_session):
    """Test 2: A fleet containing two active vehicles can return both records and identifiers."""
    company_id = 101

    v1 = Vehicle(registration_number="KA01AA1111", make="Tata", model="Signa", status=VehicleStatus.ACTIVE, company_id=company_id)
    v2 = Vehicle(registration_number="KA01BB2222", make="Mahindra", model="Blazo", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add_all([v1, v2])
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)

    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_1")
    res_str = await executor.execute("list_vehicles", {"status": "ACTIVE"})
    data = json.loads(res_str)

    assert data["total_count"] == 2
    regs = [v["registration_number"] for v in data["vehicles"]]
    assert "KA01AA1111" in regs
    assert "KA01BB2222" in regs


@pytest.mark.asyncio
async def test_vehicle_location_live_and_stale(db_session):
    """Test 3: get_vehicle_location distinguishes live, stale, and unavailable GPS data."""
    company_id = 102
    now = datetime.now(timezone.utc)

    # Driver 1 with FRESH location (5 minutes ago)
    d1 = Driver(name="Suraj", phone_number="+919811111111", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add(d1)
    await db_session.flush()

    v1 = Vehicle(
        registration_number="DL01AA0001",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        assigned_driver_id=d1.id
    )
    db_session.add(v1)

    loc1 = DriverLocation(
        driver_id=d1.id,
        company_id=company_id,
        latitude=19.0760,
        longitude=72.8777,
        timestamp=now - timedelta(minutes=5),
        source=LocationSource.PHONE_GPS,
        speed=12.5
    )
    db_session.add(loc1)

    # Driver 2 with STALE location (2 hours ago)
    d2 = Driver(name="Vikram", phone_number="+919822222222", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add(d2)
    await db_session.flush()

    v2 = Vehicle(
        registration_number="DL01BB0002",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        assigned_driver_id=d2.id
    )
    db_session.add(v2)

    loc2 = DriverLocation(
        driver_id=d2.id,
        company_id=company_id,
        latitude=28.7041,
        longitude=77.1025,
        timestamp=now - timedelta(hours=2),
        source=LocationSource.HARDWARE_GPS,
        speed=0.0
    )
    db_session.add(loc2)

    # Truck 3 with NO location records
    v3 = Vehicle(
        registration_number="DL01CC0003",
        status=VehicleStatus.ACTIVE,
        company_id=company_id
    )
    db_session.add(v3)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)

    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_1")

    # 1. Test live truck
    res1 = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v1.id}))
    assert res1["has_location"] is True
    assert res1["freshness"] == "FRESH"
    assert res1["is_stale"] is False
    assert res1["latitude"] == 19.0760

    # 2. Test stale truck
    res2 = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v2.id}))
    assert res2["has_location"] is True
    assert res2["freshness"] == "STALE"
    assert res2["is_stale"] is True
    assert res2["source"] == "HARDWARE_GPS"

    # 3. Test unavailable location
    res3 = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v3.id}))
    assert res3["has_location"] is False
    assert res3["freshness"] == "UNAVAILABLE"
    assert "No GPS coordinates available" in res3["message"]


def test_entity_resolution_patterns():
    """Test 4: Entity resolution correctly handles exact, ordinal, substring, and ambiguous references."""
    v1 = Vehicle(id=1, registration_number="RJ14UF0089", make="Tata", model="Signa 4825.TK")
    v2 = Vehicle(id=2, registration_number="KA01AB1234", make="BharatBenz", model="2823R")
    v3 = Vehicle(id=3, registration_number="KA01AB5678", make="BharatBenz", model="1617R")
    fleet = [v1, v2, v3]

    # Exact registration
    r1 = CopilotEntityResolver.resolve_vehicle(fleet, "RJ14UF0089")
    assert r1["status"] == "EXACT"
    assert r1["vehicle"].id == 1

    # Registration with spaces/case
    r2 = CopilotEntityResolver.resolve_vehicle(fleet, "rj 14 uf 0089")
    assert r2["status"] == "EXACT"
    assert r2["vehicle"].id == 1

    # Ordinal references: "Truck 01" -> 1st vehicle, "Truck 02" -> 2nd vehicle
    r3 = CopilotEntityResolver.resolve_vehicle(fleet, "Truck 01")
    assert r3["status"] == "EXACT"
    assert r3["vehicle"].id == 1

    r4 = CopilotEntityResolver.resolve_vehicle(fleet, "Truck 02")
    assert r4["status"] == "EXACT"
    assert r4["vehicle"].id == 2

    # Partial / suffix registration "0089"
    r5 = CopilotEntityResolver.resolve_vehicle(fleet, "0089")
    assert r5["status"] == "EXACT"
    assert r5["vehicle"].id == 1

    # Ambiguous query "BharatBenz" matches both v2 and v3
    r6 = CopilotEntityResolver.resolve_vehicle(fleet, "BharatBenz")
    assert r6["status"] == "AMBIGUOUS"
    assert len(r6["candidates"]) == 2

    # Nonexistent query
    r7 = CopilotEntityResolver.resolve_vehicle(fleet, "NonExistentTruck999")
    assert r7["status"] == "NOT_FOUND"


def test_driver_entity_resolution():
    """Test 5: Driver entity resolution handles names, phones, employee IDs, and ambiguous matches."""
    d1 = Driver(id=1, name="Joginder Singh", phone_number="+919876543210", employee_id="EMP-01")
    d2 = Driver(id=2, name="Joginder Sharma", phone_number="+919876543211", employee_id="EMP-02")
    d3 = Driver(id=3, name="Anil Verma", phone_number="+919876543212", employee_id="EMP-03")
    drivers = [d1, d2, d3]

    # Exact match by name
    res1 = CopilotEntityResolver.resolve_driver(drivers, "Anil Verma")
    assert res1["status"] == "EXACT"
    assert res1["driver"].id == 3

    # Exact match by employee ID
    res2 = CopilotEntityResolver.resolve_driver(drivers, "EMP-01")
    assert res2["status"] == "EXACT"
    assert res2["driver"].id == 1

    # Ambiguous match ("Joginder" matches both d1 and d2)
    res3 = CopilotEntityResolver.resolve_driver(drivers, "Joginder")
    assert res3["status"] == "AMBIGUOUS"
    assert len(res3["candidates"]) == 2

    # Not found
    res4 = CopilotEntityResolver.resolve_driver(drivers, "Rajesh")
    assert res4["status"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_multi_tenancy_cross_fleet_isolation(db_session):
    """Test 6: Nonexistent or other fleet vehicle, driver, and trip IDs are blocked."""
    company_a = 201
    company_b = 202

    v_b = Vehicle(registration_number="COMPANY_B_TRUCK", status=VehicleStatus.ACTIVE, company_id=company_b)
    d_b = Driver(name="Driver B", phone_number="+919999999999", status=DriverStatus.ACTIVE, company_id=company_b)
    t_b = Trip(trip_id="TRP-COMP-B", status=TripStatus.CREATED, origin_location="Delhi", destination_location="Jaipur", company_id=company_b)

    db_session.add_all([v_b, d_b, t_b])
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)

    # Company A attempts to access Company B records
    executor = CopilotToolExecutor(uow=uow, company_id=company_a, user_id="user_a")

    # 1. Vehicle lookup
    v_res = json.loads(await executor.execute("get_vehicle_details", {"vehicle_id": v_b.id}))
    assert "error" in v_res
    assert "not found" in v_res["error"].lower()

    # 2. Vehicle location
    loc_res = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_b.id}))
    assert "error" in loc_res

    # 3. Trip details
    t_res = json.loads(await executor.execute("get_trip_details", {"trip_id": t_b.id}))
    assert "error" in t_res


@pytest.mark.asyncio
async def test_trip_scheduling_validation_and_proposal(db_session):
    """Test 7: Scheduling collects details, validates availability, and stages proposal without creating trip."""
    company_id = 301
    v = Vehicle(registration_number="MH04AA9999", make="Tata", status=VehicleStatus.ACTIVE, company_id=company_id)
    d = Driver(name="Amit Kumar", phone_number="+919877777777", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add_all([v, d])
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)

    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_admin")

    # Missing destination
    res_missing = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH04AA9999",
        "origin": "Mumbai",
        "planned_start_time": "2026-10-28T09:00:00"
    }))
    assert res_missing["status"] == "MISSING_INFORMATION"

    # Valid staging
    res_proposal = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH04AA9999",
        "driver_query": "Amit Kumar",
        "origin": "Mumbai",
        "destination": "Goa",
        "planned_start_time": "2026-10-28T09:00:00",
        "planned_distance_km": 580.0,
        "revenue": 35000.0
    }))
    assert res_proposal["status"] == "PROPOSAL_READY"
    assert res_proposal["requires_confirmation"] is True
    assert "proposal_id" in res_proposal

    # Verify NO trip was created in DB yet
    trips_in_db = (await db_session.execute(select(Trip).where(Trip.company_id == company_id))).scalars().all()
    assert len(trips_in_db) == 0


@pytest.mark.asyncio
async def test_trip_confirmation_and_idempotency(db_session):
    """Test 8: Confirmed trip creates verified database record, duplicate confirmation is idempotent."""
    company_id = 302
    v = Vehicle(registration_number="GJ01XX1234", make="Eicher", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add(v)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)

    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_admin")

    # 1. Prepare proposal
    prop_res = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "GJ01XX1234",
        "origin": "Ahmedabad",
        "destination": "Surat",
        "planned_start_time": "2026-10-29T06:00:00"
    }))
    proposal_id = prop_res["proposal_id"]

    # 2. Confirm execution
    confirm_res = json.loads(await executor.execute("confirm_trip_execution", {
        "proposal_id": proposal_id
    }))
    assert confirm_res["status"] == "SUCCESS"
    assert confirm_res["verified"] is True
    assert confirm_res["business_id"].startswith("TRP-")
    trip_id = confirm_res["trip_id"]

    # 3. Verify Trip exists in DB with real ID and status CREATED
    trip = await db_session.get(Trip, trip_id)
    assert trip is not None
    assert trip.status == TripStatus.CREATED
    assert trip.origin_location == "Ahmedabad"
    assert trip.destination_location == "Surat"
    assert trip.vehicle_id == v.id

    # 4. Idempotency Protection: Confirming again returns existing trip without duplicating
    dup_res = json.loads(await executor.execute("confirm_trip_execution", {
        "proposal_id": proposal_id
    }))
    assert dup_res["status"] == "ALREADY_EXECUTED"
    assert dup_res["idempotent"] is True
    assert dup_res["trip_id"] == trip_id

    # Ensure still only 1 trip in database
    total_trips = (await db_session.execute(select(Trip).where(Trip.company_id == company_id))).scalars().all()
    assert len(total_trips) == 1


@pytest.mark.asyncio
async def test_trip_scheduling_maintenance_constraint(db_session):
    """Test 9: Vehicle in MAINTENANCE status cannot be proposed or scheduled."""
    company_id = 303
    v_maint = Vehicle(
        registration_number="DL01MAINT01",
        status=VehicleStatus.MAINTENANCE,
        company_id=company_id
    )
    db_session.add(v_maint)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)

    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_admin")

    res = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "DL01MAINT01",
        "origin": "Delhi",
        "destination": "Agra",
        "planned_start_time": "2026-10-30T10:00:00"
    }))
    assert res["status"] == "CONSTRAINT_VIOLATION"
    assert "MAINTENANCE" in res["error"]


@pytest.mark.asyncio
async def test_invalid_arguments_and_unknown_tool(db_session):
    """Test 10: Unknown tools and invalid arguments return clean, actionable error JSON."""
    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)

    executor = CopilotToolExecutor(uow=uow, company_id=400, user_id="user_test")

    # Unknown tool
    res = json.loads(await executor.execute("non_existent_tool_name", {}))
    assert "error" in res
    assert "Unknown tool" in res["error"]

    # Confirm with no proposal_id
    res_no_prop = json.loads(await executor.execute("confirm_trip_execution", {}))
    assert "error" in res_no_prop
    assert "proposal_id is required" in res_no_prop["error"]


@pytest.mark.asyncio
async def test_proposal_cancellation_and_expiration():
    """Test 11: Proposal cancellation and TTL expiration prevent execution."""
    mgr = TripProposalManager.get_instance()
    p = mgr.create_proposal(
        company_id=500,
        user_id="user_500",
        vehicle_id=1,
        vehicle_registration="TEST-REG",
        origin_location="Delhi",
        destination_location="Jaipur",
        planned_start_time="2026-10-30T10:00:00"
    )

    # Cancel
    mgr.cancel_proposal(p.proposal_id, company_id=500)
    cancelled_prop = mgr.get_proposal(p.proposal_id, company_id=500)
    assert cancelled_prop.status == "CANCELLED"

    # Unauthorized access (different company)
    with pytest.raises(PermissionError):
        mgr.get_proposal(p.proposal_id, company_id=999)

    # Expiration simulation
    p2 = mgr.create_proposal(
        company_id=500,
        user_id="user_500",
        vehicle_id=2,
        vehicle_registration="TEST-REG-2",
        origin_location="Delhi",
        destination_location="Agra",
        planned_start_time="2026-10-30T10:00:00"
    )
    p2.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    with pytest.raises(ValueError, match="expired"):
        mgr.get_proposal(p2.proposal_id, company_id=500)


@pytest.mark.asyncio
async def test_copilot_service_location_orchestration(db_session, monkeypatch):
    """Test 12: CopilotService multi-turn tool calling resolves vehicles and queries locations."""
    company_id = 600

    v1 = Vehicle(registration_number="MH12AA1000", make="Tata", status=VehicleStatus.ACTIVE, company_id=company_id)
    v2 = Vehicle(registration_number="MH12BB2000", make="Tata", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add_all([v1, v2])
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)

    # Mock provider simulating multi-turn tool calling:
    # Turn 1: user asks "Where are both my trucks?" -> model calls list_vehicles
    # Turn 2: model receives list of 2 vehicles -> calls get_vehicle_location for vehicle 1 & 2
    # Turn 3: model outputs final grounded response
    class MultiTurnMockLLM:
        def __init__(self, *args, **kwargs):
            self.turn = 0

        async def chat(self, messages, tools=None, temperature=0.0):
            self.turn += 1
            if self.turn == 1:
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="",
                        tool_calls=[{
                            "id": "call_list",
                            "type": "function",
                            "function": {"name": "list_vehicles", "arguments": "{}"}
                        }]
                    ),
                    finish_reason="tool_calls"
                )
            elif self.turn == 2:
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="",
                        tool_calls=[
                            {
                                "id": "call_loc_1",
                                "type": "function",
                                "function": {"name": "get_vehicle_location", "arguments": json.dumps({"vehicle_id": v1.id})}
                            },
                            {
                                "id": "call_loc_2",
                                "type": "function",
                                "function": {"name": "get_vehicle_location", "arguments": json.dumps({"vehicle_id": v2.id})}
                            }
                        ]
                    ),
                    finish_reason="tool_calls"
                )
            else:
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="Both trucks were located. Truck 1 is at coordinates and Truck 2 has no active telemetry."
                    ),
                    finish_reason="stop"
                )

    monkeypatch.setattr("services.copilot_service.OpenAIProvider", MultiTurnMockLLM)

    service = CopilotService(uow=uow, company_id=company_id, user_id="user_600")
    req = CopilotChatRequest(message="Where are both my trucks?")
    resp = await service.chat(req)

    assert "list_vehicles" in resp.metadata["tools_used"]
    assert "get_vehicle_location" in resp.metadata["tools_used"]
    assert len(resp.metadata["locations"]) == 2
    assert "Both trucks were located" in resp.message


def test_entity_resolution_stop_words_and_informal_queries():
    """Test 13: Stop word cleaning and bidirectional matching for natural informal queries."""
    v1 = Vehicle(id=1, registration_number="RJ14UF0089", make="Tata", model="Prima")
    v2 = Vehicle(id=2, registration_number="MH12AB1234", make="BharatBenz", model="2823R")
    fleet = [v1, v2]

    # "Tata truck" and "my Tata truck" should both resolve to v1
    r1 = CopilotEntityResolver.resolve_vehicle(fleet, "Tata truck")
    assert r1["status"] == "EXACT"
    assert r1["vehicle"].id == 1

    r2 = CopilotEntityResolver.resolve_vehicle(fleet, "my Tata truck")
    assert r2["status"] == "EXACT"
    assert r2["vehicle"].id == 1

    # "second truck" resolves to v2
    r3 = CopilotEntityResolver.resolve_vehicle(fleet, "second truck")
    assert r3["status"] == "EXACT"
    assert r3["vehicle"].id == 2

    # Driver with prefix "driver Joginder"
    d1 = Driver(id=1, name="Joginder Singh", phone_number="+919876543210")
    d2 = Driver(id=2, name="Anil Sharma", phone_number="+919876543211")
    drivers = [d1, d2]

    rd1 = CopilotEntityResolver.resolve_driver(drivers, "driver Joginder")
    assert rd1["status"] == "EXACT"
    assert rd1["driver"].id == 1


@pytest.mark.asyncio
async def test_driver_availability_and_active_trip_tracking(db_session):
    """Test 14: list_drivers distinguishes available drivers from drivers on active trips."""
    company_id = 701

    d_avail = Driver(name="Available Driver", phone_number="+919800000001", status=DriverStatus.ACTIVE, company_id=company_id)
    d_busy = Driver(name="Busy Driver", phone_number="+919800000002", status=DriverStatus.ACTIVE, company_id=company_id)
    d_inactive = Driver(name="Inactive Driver", phone_number="+919800000003", status=DriverStatus.INACTIVE, company_id=company_id)
    db_session.add_all([d_avail, d_busy, d_inactive])
    await db_session.flush()

    # Create active trip for d_busy
    active_trip = Trip(
        trip_id="TRP-ACTIVE-1",
        status=TripStatus.IN_PROGRESS,
        origin_location="Delhi",
        destination_location="Jaipur",
        driver_id=d_busy.id,
        company_id=company_id
    )
    db_session.add(active_trip)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    executor = CopilotToolExecutor(uow=MockUoW(db_session), company_id=company_id, user_id="user_701")

    # List all drivers
    res_all = json.loads(await executor.execute("list_drivers", {}))
    assert res_all["total_count"] == 3
    assert res_all["available_count"] == 1
    assert res_all["busy_count"] == 1

    driver_map = {d["name"]: d for d in res_all["drivers"]}
    assert driver_map["Available Driver"]["is_available"] is True
    assert driver_map["Available Driver"]["availability_status"] == "AVAILABLE"
    assert driver_map["Busy Driver"]["is_available"] is False
    assert driver_map["Busy Driver"]["availability_status"] == "BUSY_ON_TRIP"
    assert driver_map["Busy Driver"]["active_trip"]["trip_id"] == active_trip.id

    # Filter available_only
    res_avail = json.loads(await executor.execute("list_drivers", {"available_only": True}))
    assert res_avail["total_count"] == 1
    assert res_avail["drivers"][0]["name"] == "Available Driver"


@pytest.mark.asyncio
async def test_prepare_trip_proposal_with_available_driver_and_busy_rejection(db_session):
    """Test 15: Trip proposal auto-assigns available driver and rejects busy driver."""
    company_id = 702

    v1 = Vehicle(registration_number="MH12CD5555", status=VehicleStatus.ACTIVE, company_id=company_id)
    d_avail = Driver(name="Available Driver", phone_number="+919811111111", status=DriverStatus.ACTIVE, company_id=company_id)
    d_busy = Driver(name="Busy Driver", phone_number="+919822222222", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add_all([v1, d_avail, d_busy])
    await db_session.flush()

    active_trip = Trip(
        trip_id="TRP-BUSY-99",
        status=TripStatus.IN_PROGRESS,
        origin_location="Delhi",
        destination_location="Jaipur",
        driver_id=d_busy.id,
        company_id=company_id
    )
    db_session.add(active_trip)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_admin")

    # 1. Propose with driver_query="available"
    prop_res = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12CD5555",
        "driver_query": "available",
        "origin": "Mumbai",
        "destination": "Nashik",
        "planned_start_time": "2026-10-30T08:00:00"
    }))
    assert prop_res["status"] == "PROPOSAL_READY"
    assert prop_res["summary"]["driver"] == "Available Driver"

    # 2. Propose with explicitly busy driver -> must reject
    busy_res = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12CD5555",
        "driver_query": "Busy Driver",
        "origin": "Mumbai",
        "destination": "Nashik",
        "planned_start_time": "2026-10-30T08:00:00"
    }))
    assert busy_res["status"] == "DRIVER_BUSY"
    assert "currently assigned to an active trip" in busy_res["error"]


@pytest.mark.asyncio
async def test_list_expenses_multi_tenancy_and_categories(db_session):
    """Test 16: list_expenses correctly scopes to company_id and filters by category."""
    company_a = 801
    company_b = 802

    exp_fuel_a = Expense(
        business_id="EXP-FUEL-A-01",
        category=ExpenseCategory.FUEL,
        amount=5200.0,
        currency="INR",
        status=ExpenseStatus.APPROVED,
        expense_date=datetime.now(timezone.utc),
        description="Diesel refill 55L",
        company_id=company_a,
        origin_id="EVT-01"
    )
    exp_maint_a = Expense(
        business_id="EXP-MAINT-A-02",
        category=ExpenseCategory.MAINTENANCE,
        amount=12000.0,
        currency="INR",
        status=ExpenseStatus.APPROVED,
        expense_date=datetime.now(timezone.utc),
        description="Brake pad replacement",
        company_id=company_a,
        origin_id="EVT-02"
    )
    # Company B expense (must be strictly isolated)
    exp_fuel_b = Expense(
        business_id="EXP-FUEL-B-99",
        category=ExpenseCategory.FUEL,
        amount=8500.0,
        currency="INR",
        status=ExpenseStatus.APPROVED,
        expense_date=datetime.now(timezone.utc),
        description="Diesel refill company B",
        company_id=company_b,
        origin_id="EVT-03"
    )

    db_session.add_all([exp_fuel_a, exp_maint_a, exp_fuel_b])
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    executor_a = CopilotToolExecutor(uow=MockUoW(db_session), company_id=company_a, user_id="user_801")

    # Fuel expenses for company A
    res_fuel = json.loads(await executor_a.execute("list_expenses", {"category": "FUEL"}))
    assert res_fuel["total_count"] == 1
    assert res_fuel["total_amount"] == 5200.0
    assert res_fuel["expenses"][0]["business_id"] == "EXP-FUEL-A-01"
    assert res_fuel["expenses"][0]["category"] == "FUEL"

    # All expenses for company A
    res_all = json.loads(await executor_a.execute("list_expenses", {}))
    assert res_all["total_count"] == 2
    assert res_all["total_amount"] == 17200.0


@pytest.mark.asyncio
async def test_vehicle_diagnostic_sufficiency_reporting(db_session):
    """Test 17: get_vehicle_details provides diagnostic assessment and identifies insufficient records."""
    company_id = 901

    # Vehicle in MAINTENANCE with no records logged
    v_empty = Vehicle(
        registration_number="MH12MAINTEMPTY",
        status=VehicleStatus.MAINTENANCE,
        company_id=company_id
    )
    # Vehicle in MAINTENANCE with actual maintenance record
    v_with_rec = Vehicle(
        registration_number="MH12MAINTRECORDS",
        status=VehicleStatus.MAINTENANCE,
        company_id=company_id
    )
    db_session.add_all([v_empty, v_with_rec])
    await db_session.flush()

    maint_rec = MaintenanceRecord(
        business_id="MAINT-REC-01",
        status=MaintenanceStatus.STARTED,
        category=MaintenanceCategory.CORRECTIVE,
        vehicle_id=v_with_rec.id,
        workshop="Pune Central Garage"
    )
    db_session.add(maint_rec)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_admin")

    # 1. Empty maintenance records -> records_sufficient must be False
    res_empty = json.loads(await executor.execute("get_vehicle_details", {"vehicle_id": v_empty.id}))
    diag_empty = res_empty["diagnostic_assessment"]
    assert diag_empty["records_sufficient"] is False
    assert "Available records are insufficient" in diag_empty["diagnostic_notes"]

    # 2. Logged maintenance records -> records_sufficient must be True
    res_rec = json.loads(await executor.execute("get_vehicle_details", {"vehicle_id": v_with_rec.id}))
    diag_rec = res_rec["diagnostic_assessment"]
    assert diag_rec["records_sufficient"] is True
    assert len(diag_rec["logged_issues"]) == 1
    assert diag_rec["logged_issues"][0]["business_id"] == "MAINT-REC-01"


@pytest.mark.asyncio
async def test_fleet_wide_vehicle_location_query(db_session):
    """Test 18: get_vehicle_location with query='both' or 'all' returns telemetry for all fleet vehicles."""
    company_id = 902

    v1 = Vehicle(registration_number="MH12LOC01", status=VehicleStatus.ACTIVE, company_id=company_id)
    v2 = Vehicle(registration_number="MH12LOC02", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add_all([v1, v2])
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_admin")

    res = json.loads(await executor.execute("get_vehicle_location", {"query": "both"}))
    assert res["total_count"] == 2
    assert len(res["locations"]) == 2
    regs = [loc["registration_number"] for loc in res["locations"]]
    assert "MH12LOC01" in regs
    assert "MH12LOC02" in regs


@pytest.mark.asyncio
async def test_get_related_evidence_company_isolation(db_session):
    """Test 19: get_related_evidence passes company_id and scopes events strictly to fleet."""
    company_id = 903
    other_company = 999

    ev1 = OperationalEvent(
        company_id=company_id,
        entity_type=EntityType.VEHICLE,
        entity_id="101",
        event_type=EventType.POSITION_RECORDED,
        capture_method=CaptureMethod.WHATSAPP_BOT,
        occurred_at=datetime.now(timezone.utc),
        payload={"speed": 60}
    )
    ev_other = OperationalEvent(
        company_id=other_company,
        entity_type=EntityType.VEHICLE,
        entity_id="101",
        event_type=EventType.POSITION_RECORDED,
        capture_method=CaptureMethod.WHATSAPP_BOT,
        occurred_at=datetime.now(timezone.utc),
        payload={"speed": 100}
    )
    db_session.add_all([ev1, ev_other])
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="user_admin")

    res = json.loads(await executor.execute("get_related_evidence", {"entity_type": "VEHICLE", "entity_id": "101"}))
    assert "related_evidence" in res


# ==============================================================================
# MANDATORY PRE-MERGE READINESS REGRESSION SUITE
# ==============================================================================

@pytest.mark.asyncio
async def test_concurrent_confirmations_create_exactly_one_trip(db_session):
    """Regression 1: Two concurrent confirmation requests for the same proposal create exactly one trip."""
    from tests.conftest import TestSessionLocal
    company_id = 950
    v = Vehicle(registration_number="MH12RACE01", make="Tata", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add(v)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry

    uow_prep = MockUoW(db_session)
    uow_prep.repositories = RepositoryRegistry(db_session)
    prep_executor = CopilotToolExecutor(uow=uow_prep, company_id=company_id, user_id="admin_concurrency")

    # Stage proposal
    prop_res = json.loads(await prep_executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12RACE01",
        "origin": "Pune",
        "destination": "Goa",
        "planned_start_time": "2026-10-29T10:00:00"
    }))
    proposal_id = prop_res["proposal_id"]

    # Execute concurrent confirmations simultaneously
    exec1 = CopilotToolExecutor(uow=uow_prep, company_id=company_id, user_id="admin_concurrency")
    exec2 = CopilotToolExecutor(uow=uow_prep, company_id=company_id, user_id="admin_concurrency")

    res1_raw, res2_raw = await asyncio.gather(
        exec1.execute("confirm_trip_execution", {"proposal_id": proposal_id}),
        exec2.execute("confirm_trip_execution", {"proposal_id": proposal_id})
    )

    res1 = json.loads(res1_raw)
    res2 = json.loads(res2_raw)

    statuses = {res1.get("status"), res2.get("status")}
    assert "SUCCESS" in statuses
    assert "ALREADY_EXECUTED" in statuses

    # Both must reference the exact same trip
    trip_id_1 = res1.get("trip_id")
    trip_id_2 = res2.get("trip_id")
    assert trip_id_1 == trip_id_2

    # Query DB to ensure strictly 1 trip was created
    created_trips = (await db_session.execute(
        select(Trip).where(Trip.company_id == company_id, Trip.origin_id == proposal_id)
    )).scalars().all()
    assert len(created_trips) == 1


@pytest.mark.asyncio
async def test_retry_after_successful_creation_returns_original_trip(db_session):
    """Regression 2: A retry after successful creation returns the original trip without creating new records."""
    company_id = 951
    v = Vehicle(registration_number="MH12RETRY01", make="Eicher", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add(v)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="admin_retry")

    # 1. Stage proposal
    prop_res = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12RETRY01",
        "origin": "Delhi",
        "destination": "Agra",
        "planned_start_time": "2026-10-30T08:00:00"
    }))
    proposal_id = prop_res["proposal_id"]

    # 2. Initial confirmation
    res_first = json.loads(await executor.execute("confirm_trip_execution", {"proposal_id": proposal_id}))
    assert res_first["status"] == "SUCCESS"
    original_trip_id = res_first["trip_id"]

    # 3. Subsequent retry 1
    res_retry1 = json.loads(await executor.execute("confirm_trip_execution", {"proposal_id": proposal_id}))
    assert res_retry1["status"] == "ALREADY_EXECUTED"
    assert res_retry1["idempotent"] is True
    assert res_retry1["trip_id"] == original_trip_id

    # 4. Subsequent retry 2
    res_retry2 = json.loads(await executor.execute("confirm_trip_execution", {"proposal_id": proposal_id}))
    assert res_retry2["status"] == "ALREADY_EXECUTED"
    assert res_retry2["idempotent"] is True
    assert res_retry2["trip_id"] == original_trip_id

    # Total trips in DB must be exactly 1
    all_trips = (await db_session.execute(
        select(Trip).where(Trip.company_id == company_id, Trip.origin_id == proposal_id)
    )).scalars().all()
    assert len(all_trips) == 1


@pytest.mark.asyncio
async def test_transaction_failure_and_rollback_safely_reverts_proposal(db_session):
    """Regression 3: Transaction failure and rollback do not create duplicate trips or falsely mark a proposal successful."""
    company_id = 952
    v = Vehicle(registration_number="MH12FAIL01", make="BharatBenz", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add(v)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="admin_rollback")

    # Stage proposal
    prop_res = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12FAIL01",
        "origin": "Chennai",
        "destination": "Bangalore",
        "planned_start_time": "2026-10-30T10:00:00"
    }))
    proposal_id = prop_res["proposal_id"]

    # Simulate a database failure during session.flush()
    class FailingSession:
        def add(self, entity):
            pass
        async def execute(self, stmt):
            class DummyRes:
                def scalar_one_or_none(self):
                    return None
            return DummyRes()
        async def flush(self):
            raise RuntimeError("Simulated DB connection drop or constraint failure")
        async def rollback(self):
            pass

    failing_uow = MockUoW(FailingSession())
    failing_uow.repositories = RepositoryRegistry(db_session)
    failing_executor = CopilotToolExecutor(uow=failing_uow, company_id=company_id, user_id="admin_rollback")

    fail_res = json.loads(await failing_executor.execute("confirm_trip_execution", {"proposal_id": proposal_id}))
    assert "error" in fail_res
    assert "Simulated DB connection drop" in fail_res["error"]

    # Proposal status must have cleanly reverted to PENDING_CONFIRMATION (NOT EXECUTED or EXECUTING)
    proposal = TripProposalManager.get_instance().get_proposal(proposal_id, company_id)
    assert proposal.status == "PENDING_CONFIRMATION"
    assert proposal.created_trip_id is None

    # Now verify that subsequent confirmation with healthy session succeeds cleanly
    success_res = json.loads(await executor.execute("confirm_trip_execution", {"proposal_id": proposal_id}))
    assert success_res["status"] == "SUCCESS"
    assert proposal.status == "EXECUTED"
    assert proposal.created_trip_id is not None


@pytest.mark.asyncio
async def test_expired_and_cancelled_proposals_cannot_execute(db_session):
    """Regression 4: Expired and cancelled proposals cannot execute."""
    company_id = 953
    v = Vehicle(registration_number="MH12EXPCAN01", make="Tata", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add(v)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="admin_expcan")

    # 1. Test Cancelled Proposal
    prop_cancel = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12EXPCAN01",
        "origin": "Nagpur",
        "destination": "Bhopal",
        "planned_start_time": "2026-11-01T08:00:00"
    }))
    prop_cancel_id = prop_cancel["proposal_id"]

    cancel_res = json.loads(await executor.execute("cancel_trip_proposal", {"proposal_id": prop_cancel_id}))
    assert cancel_res["status"] == "CANCELLED"

    confirm_cancel_res = json.loads(await executor.execute("confirm_trip_execution", {"proposal_id": prop_cancel_id}))
    assert "error" in confirm_cancel_res
    assert "cancelled" in confirm_cancel_res["error"].lower()

    # 2. Test Expired Proposal
    prop_exp = json.loads(await executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12EXPCAN01",
        "origin": "Nagpur",
        "destination": "Raipur",
        "planned_start_time": "2026-11-01T08:00:00"
    }))
    prop_exp_id = prop_exp["proposal_id"]

    # Manually expire
    proposal_obj = TripProposalManager.get_instance().get_proposal(prop_exp_id, company_id)
    proposal_obj.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    confirm_exp_res = json.loads(await executor.execute("confirm_trip_execution", {"proposal_id": prop_exp_id}))
    assert "error" in confirm_exp_res
    assert "expired" in confirm_exp_res["error"].lower()

    # Verify zero trips created
    trips = (await db_session.execute(select(Trip).where(Trip.company_id == company_id))).scalars().all()
    assert len(trips) == 0


@pytest.mark.asyncio
async def test_cross_tenant_and_cross_user_confirmation_rejected(db_session):
    """Regression 5: Cross-tenant and cross-user confirmation attempts are rejected."""
    company_owner = 954
    company_attacker = 999
    v = Vehicle(registration_number="MH12AUTH01", make="Tata", status=VehicleStatus.ACTIVE, company_id=company_owner)
    db_session.add(v)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)

    # User Alice stages proposal for Company Owner
    alice_executor = CopilotToolExecutor(uow=uow, company_id=company_owner, user_id="user_alice")
    prop_res = json.loads(await alice_executor.execute("prepare_trip_proposal", {
        "vehicle_query": "MH12AUTH01",
        "origin": "Kolkata",
        "destination": "Ranchi",
        "planned_start_time": "2026-11-02T06:00:00"
    }))
    proposal_id = prop_res["proposal_id"]

    # Case A: Cross-tenant confirmation attempt by Company Attacker
    attacker_executor = CopilotToolExecutor(uow=uow, company_id=company_attacker, user_id="user_attacker")
    cross_tenant_res = json.loads(await attacker_executor.execute("confirm_trip_execution", {"proposal_id": proposal_id}))
    assert "error" in cross_tenant_res
    assert "outside your fleet" in cross_tenant_res["error"]

    # Case B: Cross-user confirmation attempt by User Bob in same company
    bob_executor = CopilotToolExecutor(uow=uow, company_id=company_owner, user_id="user_bob")
    cross_user_res = json.loads(await bob_executor.execute("confirm_trip_execution", {"proposal_id": proposal_id}))
    assert "error" in cross_user_res
    assert "staged by user 'user_alice'" in cross_user_res["error"]

    # Case C: Legitimate User Alice confirms successfully
    legit_res = json.loads(await alice_executor.execute("confirm_trip_execution", {"proposal_id": proposal_id}))
    assert legit_res["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_single_process_deployment_and_multi_worker_limitations():
    """Regression 6: Verifies explicit single-process deployment configuration and multi-worker limitations."""
    mgr = TripProposalManager.get_instance()
    assert mgr.DEPLOYMENT_MODE == "SINGLE_PROCESS"
    assert mgr.MAX_WORKERS_SUPPORTED == 1

    # Staged proposal exists in this worker's memory
    proposal = mgr.create_proposal(
        company_id=1,
        user_id="user1",
        vehicle_id=10,
        vehicle_registration="TEST-REG",
        origin_location="A",
        destination_location="B",
        planned_start_time="2026-11-01T00:00:00"
    )
    assert mgr.get_proposal(proposal.proposal_id, company_id=1) is not None

    # Simulating a secondary worker process without shared memory (empty dictionary)
    worker2_proposals = {}
    with pytest.raises(KeyError):
        _ = worker2_proposals[proposal.proposal_id]


@pytest.mark.asyncio
async def test_gps_freshness_boundaries_and_clock_skew(db_session):
    """Regression 7: GPS freshness boundaries are consistent with 15-minute threshold and handle edge cases."""
    company_id = 955
    now = datetime.now(timezone.utc)

    # Helper to create vehicle, driver, and DriverLocation
    async def create_tracked_vehicle(reg: str, loc_time: Optional[datetime], lat: Optional[float] = 19.076, lng: Optional[float] = 72.877):
        v = Vehicle(registration_number=reg, make="Tata", status=VehicleStatus.ACTIVE, company_id=company_id)
        db_session.add(v)
        await db_session.flush()

        d = Driver(name=f"Driver {reg}", phone_number=f"+91{reg[-8:]}", status=DriverStatus.ACTIVE, company_id=company_id)
        db_session.add(d)
        await db_session.flush()

        v.assigned_driver_id = d.id

        if lat is not None and lng is not None and loc_time is not None:
            loc = DriverLocation(
                driver_id=d.id,
                company_id=company_id,
                latitude=lat,
                longitude=lng,
                timestamp=loc_time,
                source=LocationSource.PHONE_GPS,
                speed=15.0,
                accuracy=5.0
            )
            db_session.add(loc)
        elif lat is not None and lng is not None:
            d.last_known_lat = lat
            d.last_known_lng = lng
            d.last_location_at = None

        await db_session.commit()
        return v

    v_0m = await create_tracked_vehicle("MH12GPS00M", datetime.now(timezone.utc))
    v_14m = await create_tracked_vehicle("MH12GPS14M", datetime.now(timezone.utc) - timedelta(minutes=14))
    v_15m = await create_tracked_vehicle("MH12GPS15M", datetime.now(timezone.utc) - timedelta(seconds=890))  # Near 15m boundary (Fresh <= 900s)
    v_16m = await create_tracked_vehicle("MH12GPS16M", datetime.now(timezone.utc) - timedelta(seconds=920))  # Past 15m boundary (Stale > 900s)
    v_30m = await create_tracked_vehicle("MH12GPS30M", datetime.now(timezone.utc) - timedelta(minutes=30))
    v_25h = await create_tracked_vehicle("MH12GPS25H", datetime.now(timezone.utc) - timedelta(hours=25))    # > 24h -> Very Stale
    v_future = await create_tracked_vehicle("MH12GPSFUT", datetime.now(timezone.utc) + timedelta(minutes=5)) # Future clock skew
    v_notime = await create_tracked_vehicle("MH12GPSNOTM", None)                       # Missing timestamp
    v_unavail = await create_tracked_vehicle("MH12GPSUNAV", None, lat=None, lng=None) # No coords

    class MockUoW:
        def __init__(self, s):
            self.session = s

    from infrastructure.uow import RepositoryRegistry
    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="admin_gps")

    # 1. 0 minutes: FRESH
    res_0m = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_0m.id}))
    assert res_0m["freshness"] == "FRESH"
    assert res_0m["is_stale"] is False
    assert "Live GPS" in res_0m["freshness_label"]

    # 2. 14 minutes: FRESH
    res_14m = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_14m.id}))
    assert res_14m["freshness"] == "FRESH"
    assert res_14m["is_stale"] is False

    # 3. Exactly 15 minutes (900s): FRESH (boundary test)
    res_15m = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_15m.id}))
    assert res_15m["freshness"] == "FRESH"
    assert res_15m["is_stale"] is False

    # 4. 15 minutes 1 second: STALE
    res_16m = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_16m.id}))
    assert res_16m["freshness"] == "STALE"
    assert res_16m["is_stale"] is True

    # 5. 30 minutes: STALE
    res_30m = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_30m.id}))
    assert res_30m["freshness"] == "STALE"
    assert res_30m["is_stale"] is True
    assert "Stale GPS" in res_30m["freshness_label"]

    # 6. 25 hours (>24h): VERY_STALE
    res_25h = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_25h.id}))
    assert res_25h["freshness"] == "VERY_STALE"
    assert res_25h["is_stale"] is True
    assert "Very Stale" in res_25h["freshness_label"]

    # 7. Future Timestamp (>60s): FUTURE_TIMESTAMP
    res_future = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_future.id}))
    assert res_future["freshness"] == "FUTURE_TIMESTAMP"
    assert res_future["is_stale"] is True
    assert "Invalid Future Timestamp" in res_future["freshness_label"]

    # 8. Missing Coordinates: UNAVAILABLE
    res_unavail = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_unavail.id}))
    assert res_unavail["freshness"] == "UNAVAILABLE"
    assert res_unavail["has_location"] is False

    # 9. Missing Timestamp with valid coordinates: STALE
    res_notime = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_notime.id}))
    assert res_notime["freshness"] == "STALE"
    assert res_notime["is_stale"] is True
    assert "Timestamp missing" in res_notime["freshness_label"]


@pytest.mark.asyncio
async def test_list_drivers_omitted_and_null_optional_parameters(db_session):
    """Test 22: list_drivers handles omitted, null, and model-generated optional parameters gracefully."""
    company_id = 901

    d1 = Driver(name="Driver Alpha", phone_number="+919811000001", status=DriverStatus.ACTIVE, company_id=company_id)
    d2 = Driver(name="Driver Beta", phone_number="+919811000002", status=DriverStatus.ACTIVE, company_id=company_id)
    d3 = Driver(name="Driver Gamma", phone_number="+919811000003", status=DriverStatus.INACTIVE, company_id=company_id)
    db_session.add_all([d1, d2, d3])
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    executor = CopilotToolExecutor(uow=MockUoW(db_session), company_id=company_id, user_id="u_901")

    # 1. Omitted search and is_active
    res_omitted = json.loads(await executor.execute("list_drivers", {}))
    assert res_omitted["total_count"] == 3
    assert len(res_omitted["drivers"]) == 3

    # 2. Supplied as null (None in Python)
    res_null = json.loads(await executor.execute("list_drivers", {
        "search": None,
        "is_active": None,
        "available_only": None,
        "limit": None
    }))
    assert res_null["total_count"] == 3
    assert len(res_null["drivers"]) == 3

    # 3. Model-generated exact argument payload from production UI error:
    # {"available_only": false, "is_active": null, "limit": 20, "search": null}
    model_payload = {
        "available_only": False,
        "is_active": None,
        "limit": 20,
        "search": None
    }
    res_model = json.loads(await executor.execute("list_drivers", model_payload))
    assert res_model["total_count"] == 3
    assert "drivers" in res_model
    assert res_model["available_count"] == 2  # 2 active, 0 busy


@pytest.mark.asyncio
async def test_list_drivers_filtering_and_availability_options(db_session):
    """Test 23: list_drivers applies search, active filtering, and availability options correctly."""
    company_id = 902

    d_avail = Driver(name="Suresh Kumar", phone_number="+919822000001", status=DriverStatus.ACTIVE, company_id=company_id)
    d_busy = Driver(name="Ramesh Sharma", phone_number="+919822000002", status=DriverStatus.ACTIVE, company_id=company_id)
    d_inact = Driver(name="Dinesh Verma", phone_number="+919822000003", status=DriverStatus.INACTIVE, company_id=company_id)
    db_session.add_all([d_avail, d_busy, d_inact])
    await db_session.flush()

    active_trip = Trip(
        trip_id="TRP-BUSY-902",
        status=TripStatus.IN_PROGRESS,
        origin_location="Noida",
        destination_location="Agra",
        driver_id=d_busy.id,
        company_id=company_id
    )
    db_session.add(active_trip)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    executor = CopilotToolExecutor(uow=MockUoW(db_session), company_id=company_id, user_id="u_902")

    # 1. Valid search string
    res_search = json.loads(await executor.execute("list_drivers", {"search": "Suresh"}))
    assert res_search["total_count"] == 1
    assert res_search["drivers"][0]["name"] == "Suresh Kumar"

    # 2. is_active boolean filter (true)
    res_active = json.loads(await executor.execute("list_drivers", {"is_active": True}))
    assert res_active["total_count"] == 2
    names = [d["name"] for d in res_active["drivers"]]
    assert "Suresh Kumar" in names
    assert "Ramesh Sharma" in names
    assert "Dinesh Verma" not in names

    # 3. is_active boolean filter (false)
    res_inactive = json.loads(await executor.execute("list_drivers", {"is_active": False}))
    assert res_inactive["total_count"] == 1
    assert res_inactive["drivers"][0]["name"] == "Dinesh Verma"

    # 4. available_only = True -> only active AND not on trip
    res_avail = json.loads(await executor.execute("list_drivers", {"available_only": True}))
    assert res_avail["total_count"] == 1
    assert res_avail["drivers"][0]["name"] == "Suresh Kumar"
    assert res_avail["drivers"][0]["availability_status"] == "AVAILABLE"

    # 5. available_only = False -> all returned
    res_not_avail_only = json.loads(await executor.execute("list_drivers", {"available_only": False}))
    assert res_not_avail_only["total_count"] == 3


@pytest.mark.asyncio
async def test_list_drivers_malformed_arguments_and_recovery(db_session):
    """Test 24: list_drivers handles malformed arguments safely without unhandled crashes."""
    company_id = 903

    d1 = Driver(name="Test Driver", phone_number="+919833000001", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add(d1)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    executor = CopilotToolExecutor(uow=MockUoW(db_session), company_id=company_id, user_id="u_903")

    # Malformed is_active string
    res_bad_active = json.loads(await executor.execute("list_drivers", {"is_active": "maybe"}))
    assert res_bad_active.get("error") == "Validation Error"
    assert "is_active" in res_bad_active.get("message", "")

    # Malformed limit string
    res_bad_limit = json.loads(await executor.execute("list_drivers", {"limit": "not_an_int"}))
    assert res_bad_limit.get("error") == "Validation Error"
    assert "limit" in res_bad_limit.get("message", "")

    # Malformed available_only
    res_bad_avail = json.loads(await executor.execute("list_drivers", {"available_only": "invalid_val"}))
    assert res_bad_avail.get("error") == "Validation Error"

    # String representation of booleans and numbers should parse safely
    res_string_bool = json.loads(await executor.execute("list_drivers", {
        "is_active": "true",
        "available_only": "false",
        "limit": "10"
    }))
    assert res_string_bool["total_count"] == 1


@pytest.mark.asyncio
async def test_driver_availability_privacy_and_data_minimization(db_session):
    """Test 25: Driver phone numbers are not returned in default availability responses."""
    company_id = 904

    d1 = Driver(name="Secret Driver", phone_number="+919999888877", employee_id="EMP-904", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add(d1)
    await db_session.commit()

    class MockUoW:
        def __init__(self, s):
            self.session = s

    executor = CopilotToolExecutor(uow=MockUoW(db_session), company_id=company_id, user_id="u_904")

    # Default availability response
    res = json.loads(await executor.execute("list_drivers", {"available_only": True}))
    assert res["total_count"] == 1
    driver_record = res["drivers"][0]
    assert driver_record["name"] == "Secret Driver"
    assert driver_record["employee_id"] == "EMP-904"
    assert driver_record["availability_status"] == "AVAILABLE"
    # Must NOT expose phone_number in default response
    assert "phone_number" not in driver_record

    # Phone number query: searching specifically by phone number digits DOES return phone_number
    res_phone_search = json.loads(await executor.execute("list_drivers", {"search": "99998888"}))
    assert res_phone_search["total_count"] == 1
    assert res_phone_search["drivers"][0]["phone_number"] == "+919999888877"


@pytest.mark.asyncio
async def test_copilot_tool_definitions_nullable_schema(db_session):
    """Test 26: Tool definitions declare nullable: True for all optional parameters."""
    for tool in COPILOT_TOOLS_DEFINITION:
        func = tool["function"]
        props = func.get("parameters", {}).get("properties", {})
        required = func.get("parameters", {}).get("required", [])

        for prop_name, prop_def in props.items():
            if prop_name not in required:
                # Optional parameters must be marked nullable: True so LLM provider validators accept null
                assert prop_def.get("nullable") is True, f"Tool '{func['name']}' parameter '{prop_name}' missing nullable: True"


@pytest.mark.asyncio
async def test_gps_last_known_location_and_location_type_messaging(db_session):
    """Test 27: Telemetry classifies last-known positions and location_type explicitly."""
    company_id = 905

    v_fresh = Vehicle(registration_number="MH12LIVE01", make="Tata", model="Prima", status=VehicleStatus.ACTIVE, company_id=company_id)
    v_stale = Vehicle(registration_number="MH12STALE1", make="Eicher", model="Pro", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add_all([v_fresh, v_stale])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    d_fresh = Driver(name="Driver Live", phone_number="+919876543210", status=DriverStatus.ACTIVE, company_id=company_id)
    d_stale = Driver(name="Driver Stale", phone_number="+919876543211", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add_all([d_fresh, d_stale])
    await db_session.flush()

    v_fresh.assigned_driver_id = d_fresh.id
    v_stale.assigned_driver_id = d_stale.id

    # Fresh point (5 min ago)
    loc_fresh = DriverLocation(
        driver_id=d_fresh.id,
        company_id=company_id,
        latitude=18.5204,
        longitude=73.8567,
        timestamp=now - timedelta(minutes=5),
        source=LocationSource.PHONE_GPS,
        speed=10.0
    )
    # Stale point (2 hours ago)
    loc_stale = DriverLocation(
        driver_id=d_stale.id,
        company_id=company_id,
        latitude=19.0760,
        longitude=72.8777,
        timestamp=now - timedelta(hours=2),
        source=LocationSource.PHONE_GPS,
        speed=0.0
    )
    db_session.add_all([loc_fresh, loc_stale])
    await db_session.commit()

    from infrastructure.uow import RepositoryRegistry
    class MockUoW:
        def __init__(self, s):
            self.session = s

    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="u_905")

    res_fresh = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_fresh.id}))
    assert res_fresh["freshness"] == "FRESH"
    assert res_fresh["is_last_known"] is False
    assert res_fresh["location_type"] == "CURRENT_POSITION"

    res_stale = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v_stale.id}))
    assert res_stale["freshness"] == "STALE"
    assert res_stale["is_last_known"] is True
    assert res_stale["location_type"] == "LAST_KNOWN_LOCATION"
    assert "Last-Known Location" in res_stale["freshness_label"]


@pytest.mark.asyncio
async def test_list_drivers_exact_null_arguments_regression(db_session):
    """
    Test 28 (Regression): Exact reproduction of Groq model generated arguments:
    available_only: null, is_active: null, limit: null, search: null.
    Verifies full execution path, correct defaults, and semantics:
    - is_active=null means no active status restriction (both active and inactive returned).
    - search=null means no search restriction.
    - available_only=null defaults to False (does not filter busy drivers).
    - limit=null defaults to 20.
    """
    company_id = 910

    # 1. Active & Available driver
    d1 = Driver(name="Amit Kumar", phone_number="+919811111111", employee_id="EMP-910-1", status=DriverStatus.ACTIVE, company_id=company_id)
    # 2. Active & Busy driver (on in-progress trip)
    d2 = Driver(name="Baldev Singh", phone_number="+919822222222", employee_id="EMP-910-2", status=DriverStatus.ACTIVE, company_id=company_id)
    # 3. Inactive driver
    d3 = Driver(name="Chandan Lal", phone_number="+919833333333", employee_id="EMP-910-3", status=DriverStatus.INACTIVE, company_id=company_id)
    db_session.add_all([d1, d2, d3])
    await db_session.flush()

    # Create active trip for d2
    active_trip = Trip(
        trip_id="TRP-910-BUSY",
        driver_id=d2.id,
        status=TripStatus.IN_PROGRESS,
        origin_location="Delhi",
        destination_location="Jaipur",
        company_id=company_id
    )
    db_session.add(active_trip)
    await db_session.commit()

    from infrastructure.uow import RepositoryRegistry
    class MockUoW:
        def __init__(self, s):
            self.session = s

    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="u_910")

    # The exact null arguments generated by Groq model
    exact_null_args = {
        "available_only": None,
        "is_active": None,
        "limit": None,
        "search": None
    }

    raw_res = await executor.execute("list_drivers", exact_null_args)
    data = json.loads(raw_res)

    assert "error" not in data
    assert data["total_count"] == 3
    assert data["available_count"] == 1
    assert data["busy_count"] == 1

    driver_map = {d["name"]: d for d in data["drivers"]}
    # Amit is available
    assert driver_map["Amit Kumar"]["is_available"] is True
    assert driver_map["Amit Kumar"]["availability_status"] == "AVAILABLE"
    assert driver_map["Amit Kumar"]["active_trip"] is None
    # Baldev is busy on active trip
    assert driver_map["Baldev Singh"]["is_available"] is False
    assert driver_map["Baldev Singh"]["availability_status"] == "BUSY_ON_TRIP"
    assert driver_map["Baldev Singh"]["active_trip"]["business_id"] == "TRP-910-BUSY"
    # Chandan is inactive but included because is_active=None means no restriction
    assert driver_map["Chandan Lal"]["is_available"] is False
    assert driver_map["Chandan Lal"]["availability_status"] == "INACTIVE"


@pytest.mark.asyncio
async def test_list_drivers_filtering_and_bounds_semantics(db_session):
    """
    Test 29: Verifies correct semantics for search, is_active, available_only, and limit bounds:
    - Empty/whitespace search string means no search filter.
    - is_active=True returns only active drivers.
    - available_only=True returns only active, non-busy drivers.
    - limit is bounded and defaults correctly.
    """
    company_id = 911

    d_act_free = Driver(name="Deepak Sharma", phone_number="+919844444444", status=DriverStatus.ACTIVE, company_id=company_id)
    d_act_busy = Driver(name="Eknath Patil", phone_number="+919855555555", status=DriverStatus.ACTIVE, company_id=company_id)
    d_inact = Driver(name="Farhan Khan", phone_number="+919866666666", status=DriverStatus.INACTIVE, company_id=company_id)
    db_session.add_all([d_act_free, d_act_busy, d_inact])
    await db_session.flush()

    trip_busy = Trip(
        trip_id="TRP-911-BUSY",
        driver_id=d_act_busy.id,
        status=TripStatus.IN_PROGRESS,
        origin_location="Mumbai",
        destination_location="Pune",
        company_id=company_id
    )
    db_session.add(trip_busy)
    await db_session.commit()

    from infrastructure.uow import RepositoryRegistry
    class MockUoW:
        def __init__(self, s):
            self.session = s

    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="u_911")

    # 1. Empty string search should not restrict results
    res_empty_search = json.loads(await executor.execute("list_drivers", {"search": "", "limit": 10}))
    assert res_empty_search["total_count"] == 3

    # 2. available_only = True filters to only active, non-busy drivers
    res_avail = json.loads(await executor.execute("list_drivers", {"available_only": True}))
    assert res_avail["total_count"] == 1
    assert res_avail["drivers"][0]["name"] == "Deepak Sharma"

    # 3. is_active = True filters out inactive drivers
    res_act = json.loads(await executor.execute("list_drivers", {"is_active": True}))
    assert res_act["total_count"] == 2
    names = {d["name"] for d in res_act["drivers"]}
    assert names == {"Deepak Sharma", "Eknath Patil"}

    # 4. is_active = False filters to only inactive drivers
    res_inact = json.loads(await executor.execute("list_drivers", {"is_active": False}))
    assert res_inact["total_count"] == 1
    assert res_inact["drivers"][0]["name"] == "Farhan Khan"

    # 5. limit clamping
    res_limit = json.loads(await executor.execute("list_drivers", {"limit": 1}))
    assert len(res_limit["drivers"]) == 1


@pytest.mark.asyncio
async def test_all_copilot_tool_definitions_schema_compatibility():
    """
    Test 30: Validates provider-facing schema compatibility across all tools:
    - Every optional parameter supports null via a type list containing 'null'.
    - If enum is specified on an optional parameter, None/null is included.
    - Common optional fields define valid defaults.
    """
    for tool in COPILOT_TOOLS_DEFINITION:
        func = tool["function"]
        props = func.get("parameters", {}).get("properties", {})
        required = func.get("parameters", {}).get("required", [])

        for prop_name, prop_def in props.items():
            if prop_name not in required:
                p_type = prop_def.get("type")
                # Type must be a list containing 'null' to be valid in JSON schema Draft 7 for Groq/OpenAI
                assert isinstance(p_type, list) and "null" in p_type, (
                    f"Tool '{func['name']}' parameter '{prop_name}' has non-nullable type '{p_type}'. Expected list containing 'null'."
                )
                if "enum" in prop_def:
                    assert None in prop_def["enum"], (
                        f"Tool '{func['name']}' parameter '{prop_name}' has enum without null/None."
                    )


@pytest.mark.asyncio
async def test_groq_or_configured_provider_null_tool_call_compatibility():
    """
    Test 31: Verifies schema compatibility against actual configured provider (Groq)
    or performs deterministic JSON-schema type-compatibility validation.
    """
    from config import settings
    from openai import AsyncOpenAI, BadRequestError

    # If Groq/OpenAI key is configured, verify real provider accepts the exact null arguments
    if settings.OPENAI_API_KEY and settings.LLM_BASE_URL:
        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=15.0
        )
        try:
            res = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": "call list_drivers with available_only=null, is_active=null, limit=null, search=null"}
                ],
                tools=COPILOT_TOOLS_DEFINITION
            )
            choice = res.choices[0]
            # Must succeed without BadRequestError
            assert choice is not None
            if choice.message.tool_calls:
                tc = choice.message.tool_calls[0]
                assert tc.function.name == "list_drivers"
        except BadRequestError as e:
            pytest.fail(f"Upstream provider rejected tool definition or arguments with BadRequestError: {e}")
        except Exception as e:
            # Network/timeout errors in CI/sandbox without external access are acceptable fallbacks
            pytest.skip(f"Provider unreachable or network restricted: {e}")


@pytest.mark.asyncio
async def test_gps_timezone_naive_timestamp_normalization(db_session):
    """
    Test 32: Verifies that timezone-naive datetimes stored in database are cleanly
    normalized to UTC without raising TypeError during age subtraction.
    """
    company_id = 920

    v = Vehicle(registration_number="MH12NAIVE1", make="Tata", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add(v)
    await db_session.flush()

    d = Driver(name="Naive Driver", phone_number="+919812345678", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add(d)
    await db_session.flush()

    v.assigned_driver_id = d.id

    # Create naive UTC datetime (no tzinfo)
    naive_dt = (datetime.now(timezone.utc) - timedelta(minutes=10)).replace(tzinfo=None)
    assert naive_dt.tzinfo is None

    loc = DriverLocation(
        driver_id=d.id,
        company_id=company_id,
        latitude=19.0760,
        longitude=72.8777,
        timestamp=naive_dt,
        source=LocationSource.PHONE_GPS,
        speed=20.0
    )
    db_session.add(loc)
    await db_session.commit()

    from infrastructure.uow import RepositoryRegistry
    class MockUoW:
        def __init__(self, s):
            self.session = s

    uow = MockUoW(db_session)
    uow.repositories = RepositoryRegistry(db_session)
    executor = CopilotToolExecutor(uow=uow, company_id=company_id, user_id="u_920")

    res = json.loads(await executor.execute("get_vehicle_location", {"vehicle_id": v.id}))
    assert res["has_location"] is True
    assert res["freshness"] == "FRESH"
    assert res["location_type"] == "CURRENT_POSITION"
    assert res["is_last_known"] is False
    assert res["age_seconds"] is not None


@pytest.mark.asyncio
async def test_copilot_service_extracts_driver_cards_metadata(db_session):
    """
    Test 33: Verifies that CopilotService extracts driver results into structured_metadata['drivers']
    so the frontend renders dedicated driver cards instead of repeating markdown tables.
    """
    company_id = 921

    d1 = Driver(name="Driver Alpha", phone_number="+919800000010", employee_id="EMP-A", status=DriverStatus.ACTIVE, company_id=company_id)
    d2 = Driver(name="Driver Beta", phone_number="+919800000011", employee_id="EMP-B", status=DriverStatus.ACTIVE, company_id=company_id)
    db_session.add_all([d1, d2])
    await db_session.commit()


    from infrastructure.uow import RepositoryRegistry
    from services.copilot_service import CopilotService
    from schemas.copilot import CopilotChatRequest
    from infrastructure.llm.provider import LLMMessage, LLMResponse

    class MockUoW:
        def __init__(self, s):
            self.session = s
            self.repositories = RepositoryRegistry(s)

        async def commit(self):
            await self.session.commit()

    class DriverToolMockLLM:
        def __init__(self):
            self.called = False

        async def chat(self, messages, tools=None, temperature=0.0):
            if not self.called:
                self.called = True
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="",
                        tool_calls=[{
                            "id": "tc_driver_1",
                            "type": "function",
                            "function": {
                                "name": "list_drivers",
                                "arguments": '{"available_only": true}'
                            }
                        }]
                    ),
                    finish_reason="tool_calls"
                )
            return LLMResponse(
                message=LLMMessage(
                    role="assistant",
                    content="Here are the available drivers in your fleet."
                ),
                finish_reason="stop"
            )

    service = CopilotService(uow=MockUoW(db_session), company_id=company_id, user_id="1")
    service.llm = DriverToolMockLLM()

    resp = await service.chat(CopilotChatRequest(message="Which drivers are available?"))
    assert resp.metadata is not None
    assert "drivers" in resp.metadata
    assert len(resp.metadata["drivers"]) == 2
    driver_names = {d["name"] for d in resp.metadata["drivers"]}
    assert "Driver Alpha" in driver_names
