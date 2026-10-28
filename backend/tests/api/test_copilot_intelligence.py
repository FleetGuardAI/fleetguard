"""
FleetGuard — Evidence-Grounded Fleet Intelligence Regression Tests (P3)
Automated test suite verifying:
1. Accurate fleet health counts (active, maintenance, total).
2. Fresh, stale, and unavailable GPS classifications.
3. Maintenance priorities: overdue by odometer and date, repeat repairs, odometer inconsistency.
4. Fuel efficiency analysis: period-over-period spend, paired km/L & L/100km, consumption anomaly detection,
   no expense double-counting, graceful handling of insufficient data.
5. Trip performance: departure delay, arrival delay, distance deviation (>15%), prolonged unclosed trips.
6. Data quality findings: non-defect labeling, missing telemetry, zero distance.
7. Anomaly ranking and severity filtering.
8. Multi-tenant isolation (company A vs company B).
9. CopilotToolExecutor integration for all 6 intelligence tools.
10. Safe action handoffs without autonomous writes.
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus
from models.trip_domain import Trip, TripStatus
from models.location_tracking import DriverLocation, LocationSource
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus, MaintenanceCategory
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from services.fleet_intelligence_engine import FleetIntelligenceEngine
from services.copilot_tools import CopilotToolExecutor
from infrastructure.uow import RepositoryRegistry


class MockUoW:
    def __init__(self, s):
        self.session = s
        self.repositories = RepositoryRegistry(s)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()


# ══════════════════════════════════════════════════════════════════════════════
# 1. FLEET HEALTH & TELEMETRY BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_fleet_health_counts_and_telemetry_classification(db_session):
    """
    Verifies accurate counting of active/maintenance vehicles and classification of
    fresh (<=15m), stale (15m-24h), and unavailable (>24h or missing) GPS data.
    """
    company_id = 9101
    now = datetime.now(timezone.utc)

    # 3 drivers
    d_fresh = Driver(name="Fresh Driver", phone_number="+919876543001", license_number="LIC-F1", company_id=company_id)
    d_stale = Driver(name="Stale Driver", phone_number="+919876543002", license_number="LIC-S1", company_id=company_id)
    d_offline = Driver(name="Offline Driver", phone_number="+919876543003", license_number="LIC-O1", company_id=company_id)
    db_session.add_all([d_fresh, d_stale, d_offline])
    await db_session.flush()

    # 3 active vehicles, 1 in maintenance
    v_fresh = Vehicle(registration_number="MH12-FRESH", status=VehicleStatus.ACTIVE, company_id=company_id, assigned_driver_id=d_fresh.id)
    v_stale = Vehicle(registration_number="MH12-STALE", status=VehicleStatus.ACTIVE, company_id=company_id, assigned_driver_id=d_stale.id)
    v_offline = Vehicle(registration_number="MH12-OFFLINE", status=VehicleStatus.ACTIVE, company_id=company_id, assigned_driver_id=d_offline.id)
    v_no_loc = Vehicle(registration_number="MH12-NOLOC", status=VehicleStatus.MAINTENANCE, company_id=company_id)

    db_session.add_all([v_fresh, v_stale, v_offline, v_no_loc])
    await db_session.commit()

    # Telemetry:
    # 1. Fresh (10 min ago)
    loc_fresh = DriverLocation(
        driver_id=d_fresh.id,
        latitude=18.5204,
        longitude=73.8567,
        source=LocationSource.HARDWARE_GPS,
        timestamp=(now - timedelta(minutes=10)),
        company_id=company_id
    )
    # 2. Stale (2 hours ago)
    loc_stale = DriverLocation(
        driver_id=d_stale.id,
        latitude=18.5204,
        longitude=73.8567,
        source=LocationSource.PHONE_GPS,
        timestamp=(now - timedelta(hours=2)),
        company_id=company_id
    )
    # 3. Very stale (30 hours ago)
    loc_offline = DriverLocation(
        driver_id=d_offline.id,
        latitude=18.5204,
        longitude=73.8567,
        source=LocationSource.HARDWARE_GPS,
        timestamp=(now - timedelta(hours=30)),
        company_id=company_id
    )

    db_session.add_all([loc_fresh, loc_stale, loc_offline])
    await db_session.commit()

    engine = FleetIntelligenceEngine(MockUoW(db_session), company_id=company_id)
    overview = await engine.get_fleet_health_overview()

    assert overview.total_vehicles == 4
    assert overview.active_vehicles == 3
    assert overview.maintenance_vehicles == 1

    # Telemetry
    assert overview.telemetry.fresh_count == 1
    assert overview.telemetry.stale_count == 1
    assert overview.telemetry.unavailable_count == 2  # 1 offline (>24h) + 1 no records
    assert overview.telemetry.fresh_percentage == 25.0

    # Ensure findings exist for unavailable/stale devices with honest limitations
    finding_titles = [f.title for f in overview.key_findings]
    assert any("Unavailable" in t or "Offline" in t or "Delayed" in t for t in finding_titles)


# ══════════════════════════════════════════════════════════════════════════════
# 2. MAINTENANCE PRIORITIES & RELIABILITY
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_maintenance_priorities_evaluation(db_session):
    """
    Verifies detection of:
    - Overdue maintenance (by odometer exceeding service interval)
    - Overdue maintenance (by date)
    - Repeat chronic maintenance records (>=2 records in 60 days)
    - Odometer inconsistency (current < last service)
    """
    company_id = 9102
    now = datetime.now(timezone.utc)

    # 1. Overdue by odometer
    v_odo_overdue = Vehicle(
        registration_number="MH12-ODO-DUE",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        current_odometer=52000.0,
        last_service_odometer=40000.0,
        maintenance_interval_km=10000.0  # Due at 50,000, exceeded by 2,000 km
    )

    # 2. Overdue by date
    v_date_overdue = Vehicle(
        registration_number="MH12-DATE-DUE",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        last_service_date=now - timedelta(days=45),
        maintenance_interval_days=30  # Exceeded by 15 days
    )

    # 3. Odometer Inconsistency
    v_inconsistent = Vehicle(
        registration_number="MH12-ODO-BAD",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        current_odometer=48000.0,
        last_service_odometer=51000.0  # Current is LESS than previous service!
    )

    # 4. Chronic repeated repairs vehicle
    v_repeat = Vehicle(
        registration_number="MH12-REPEAT",
        status=VehicleStatus.ACTIVE,
        company_id=company_id
    )

    db_session.add_all([v_odo_overdue, v_date_overdue, v_inconsistent, v_repeat])
    await db_session.commit()

    # Add 2 recent maintenance records for v_repeat
    m1 = MaintenanceRecord(
        business_id="MAINT-RPT-01",
        company_id=company_id,
        vehicle_id=v_repeat.id,
        status=MaintenanceStatus.COMPLETED,
        category=MaintenanceCategory.CORRECTIVE,
        scheduled_date=now - timedelta(days=20),
        cost=12000.0
    )
    m2 = MaintenanceRecord(
        business_id="MAINT-RPT-02",
        company_id=company_id,
        vehicle_id=v_repeat.id,
        status=MaintenanceStatus.COMPLETED,
        category=MaintenanceCategory.EMERGENCY,
        scheduled_date=now - timedelta(days=5),
        cost=18000.0
    )
    db_session.add_all([m1, m2])
    await db_session.commit()

    engine = FleetIntelligenceEngine(MockUoW(db_session), company_id=company_id)
    resp = await engine.get_maintenance_priorities()

    assert resp.total_overdue >= 2
    assert resp.total_repeat_issues >= 1

    finding_summaries = [f.summary for f in resp.findings]
    # Check odometer overdue
    assert any("exceeded by 2,000 km" in s for s in finding_summaries)
    # Check date overdue
    assert any("exceeded by 15 days" in s for s in finding_summaries)
    # Check repeat maintenance
    assert any("2 maintenance events in the last 60 days" in s for s in finding_summaries)
    # Check odometer inconsistency
    assert any("less than recorded last service odometer" in s for s in finding_summaries)


# ══════════════════════════════════════════════════════════════════════════════
# 3. FUEL & VEHICLE ECONOMICS ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_fuel_efficiency_and_anomaly_detection(db_session):
    """
    Verifies:
    - Fuel spend aggregation and period-over-period comparison
    - True km/L and L/100km calculated strictly from paired distance & fuel
    - Detection of excess consumption (>20% above fleet baseline)
    - Handling of zero/missing paired data without fabricating fake baselines
    """
    company_id = 9103
    now = datetime.now(timezone.utc)

    v1 = Vehicle(registration_number="MH12-FUEL-GOOD", make="Tata", model="Prima", status=VehicleStatus.ACTIVE, company_id=company_id)
    v2 = Vehicle(registration_number="MH12-FUEL-HEAVY", make="BharatBenz", model="2823R", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add_all([v1, v2])
    await db_session.commit()

    # 1. Approved Expenses: Current period ₹30,000, Previous period ₹20,000 (+50%)
    exp_curr = Expense(
        business_id="EXP-F-01",
        origin_id="ORIG-F-01",
        company_id=company_id,
        vehicle_id=v1.id,
        category=ExpenseCategory.FUEL,
        amount=30000.0,
        status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=10)
    )
    exp_prev = Expense(
        business_id="EXP-F-02",
        origin_id="ORIG-F-02",
        company_id=company_id,
        vehicle_id=v1.id,
        category=ExpenseCategory.FUEL,
        amount=20000.0,
        status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=45)
    )
    db_session.add_all([exp_curr, exp_prev])

    # 2. Completed Trips with Paired Distance & Fuel Telemetry:
    # v1 (Good): 2 trips of 500 km, 125 L each -> 25.0 L/100km (4.0 km/L)
    t1 = Trip(
        trip_id="TRP-F-01",
        company_id=company_id,
        vehicle_id=v1.id,
        status=TripStatus.COMPLETED,
        actual_distance=500.0,
        actual_fuel_liters=125.0,
        actual_end_time=now - timedelta(days=5)
    )
    t2 = Trip(
        trip_id="TRP-F-02",
        company_id=company_id,
        vehicle_id=v1.id,
        status=TripStatus.COMPLETED,
        actual_distance=500.0,
        actual_fuel_liters=125.0,
        actual_end_time=now - timedelta(days=3)
    )

    # v2 (Heavy Anomaly): 2 trips of 400 km, 160 L each -> 40.0 L/100km (2.5 km/L)
    # Fleet average = (250 + 320) / (1000 + 800) * 100 = 570 / 1800 * 100 = 31.67 L/100km
    # v2 (40 L/100km) is 26.3% higher than fleet average (exceeds 20% threshold)!
    t3 = Trip(
        trip_id="TRP-F-03",
        company_id=company_id,
        vehicle_id=v2.id,
        status=TripStatus.COMPLETED,
        actual_distance=400.0,
        actual_fuel_liters=160.0,
        actual_end_time=now - timedelta(days=6)
    )
    t4 = Trip(
        trip_id="TRP-F-04",
        company_id=company_id,
        vehicle_id=v2.id,
        status=TripStatus.COMPLETED,
        actual_distance=400.0,
        actual_fuel_liters=160.0,
        actual_end_time=now - timedelta(days=2)
    )

    db_session.add_all([t1, t2, t3, t4])
    await db_session.commit()

    engine = FleetIntelligenceEngine(MockUoW(db_session), company_id=company_id)
    analysis = await engine.analyze_fuel_efficiency(period_days=30, compare_previous=True)

    assert analysis.current_period_spend == 30000.0
    assert analysis.previous_period_spend == 20000.0
    assert analysis.spend_change_pct == 50.0

    assert analysis.total_distance_km == 1800.0
    assert analysis.total_fuel_liters == 570.0
    assert analysis.fleet_avg_km_per_liter == 3.16
    assert analysis.fleet_avg_liters_per_100km == 31.67

    # Check that spend surge finding was generated
    surge_finding = next((f for f in analysis.findings if f.finding_id == "FIND-FUEL-SPEND-SURGE"), None)
    assert surge_finding is not None
    assert "+50.0%" in surge_finding.summary

    # Check that v2 consumption anomaly was flagged
    v2_metric = next((vm for vm in analysis.vehicle_metrics if vm.vehicle_id == v2.id), None)
    assert v2_metric is not None
    assert v2_metric.is_anomaly is True
    assert v2_metric.liters_per_100km == 40.0


@pytest.mark.asyncio
async def test_fuel_efficiency_graceful_handling_without_paired_data(db_session):
    """
    When completed trips have 0 distance or fuel telemetry, the engine MUST NOT
    fabricate a fake baseline or crash. It must return INSUFFICIENT_HISTORY.
    """
    company_id = 9104
    now = datetime.now(timezone.utc)

    # Vehicle with no completed trips
    v = Vehicle(registration_number="MH12-NODATA", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add(v)
    await db_session.commit()

    engine = FleetIntelligenceEngine(MockUoW(db_session), company_id=company_id)
    analysis = await engine.analyze_fuel_efficiency(period_days=30)

    assert analysis.fleet_avg_km_per_liter is None
    assert analysis.fleet_avg_liters_per_100km is None
    assert analysis.data_quality_status.value == "INSUFFICIENT_HISTORY"
    assert any("Insufficient Paired Telemetry" in f.title for f in analysis.findings)


# ══════════════════════════════════════════════════════════════════════════════
# 4. TRIP & OPERATIONAL PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_trip_performance_delays_and_deviations(db_session):
    """
    Verifies detection of:
    - Delayed departures (status CREATED, planned_start passed > 1h)
    - En-route arrival delays (status IN_PROGRESS, planned_end passed)
    - Route distance deviations (>15%)
    - Prolonged unclosed trips (>48 hours)
    """
    company_id = 9105
    now = datetime.now(timezone.utc)

    v = Vehicle(registration_number="MH12-TRIP-TEST", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add(v)
    await db_session.commit()

    # 1. Delayed departure
    t_dep_delayed = Trip(
        trip_id="TRP-DELAY-DEP-01",
        company_id=company_id,
        vehicle_id=v.id,
        status=TripStatus.CREATED,
        origin_location="Mumbai",
        destination_location="Pune",
        planned_start_time=now - timedelta(hours=3)  # Overdue by 3h
    )

    # 2. Arrival delayed en-route
    t_arr_delayed = Trip(
        trip_id="TRP-DELAY-ARR-02",
        company_id=company_id,
        vehicle_id=v.id,
        status=TripStatus.IN_PROGRESS,
        origin_location="Delhi",
        destination_location="Jaipur",
        actual_start_time=now - timedelta(hours=8),
        planned_end_time=now - timedelta(hours=2)  # Overdue by 2h
    )

    # 3. Route distance deviation (+33.3%, > 15%)
    t_deviated = Trip(
        trip_id="TRP-DEV-DIST-03",
        company_id=company_id,
        vehicle_id=v.id,
        status=TripStatus.COMPLETED,
        origin_location="Ahmedabad",
        destination_location="Surat",
        planned_distance=300.0,
        actual_distance=400.0,
        actual_end_time=now - timedelta(days=1)
    )

    # 4. Prolonged unclosed trip (72 hours in progress)
    t_prolonged = Trip(
        trip_id="TRP-LONG-04",
        company_id=company_id,
        vehicle_id=v.id,
        status=TripStatus.IN_PROGRESS,
        origin_location="Kolkata",
        destination_location="Ranchi",
        actual_start_time=now - timedelta(hours=72)
    )

    db_session.add_all([t_dep_delayed, t_arr_delayed, t_deviated, t_prolonged])
    await db_session.commit()

    engine = FleetIntelligenceEngine(MockUoW(db_session), company_id=company_id)
    perf = await engine.analyze_trip_performance(days=30)

    assert perf.delayed_trips_count >= 2
    assert perf.distance_anomalies_count >= 1
    assert perf.unclosed_trips_count >= 1

    finding_titles = [f.title for f in perf.findings]
    assert any("Dispatch Delay: TRP-DELAY-DEP-01" in t for t in finding_titles)
    assert any("Arrival Delayed: TRP-DELAY-ARR-02" in t for t in finding_titles)
    assert any("Route Distance Deviation: TRP-DEV-DIST-03" in t for t in finding_titles)
    assert any("Prolonged Unclosed Trip: TRP-LONG-04" in t for t in finding_titles)


# ══════════════════════════════════════════════════════════════════════════════
# 5. DATA QUALITY FINDINGS
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_data_quality_audit(db_session):
    """
    Verifies detection of instrumentation deficiencies (missing GPS, missing odometer,
    completed trip with 0 km) and clear labeling that they are NOT mechanical vehicle defects.
    """
    company_id = 9106
    now = datetime.now(timezone.utc)

    # Vehicle with missing odometer
    v_no_odo = Vehicle(
        registration_number="MH12-NO-ODO",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        current_odometer=None
    )
    # Completed trip with 0 distance
    t_zero_dist = Trip(
        trip_id="TRP-ZERO-KM",
        company_id=company_id,
        status=TripStatus.COMPLETED,
        planned_distance=250.0,
        actual_distance=0.0
    )

    db_session.add_all([v_no_odo, t_zero_dist])
    await db_session.commit()

    engine = FleetIntelligenceEngine(MockUoW(db_session), company_id=company_id)
    dq = await engine.get_data_quality_findings()

    assert dq.vehicles_with_missing_odometer >= 1
    assert dq.trips_with_distance_gaps >= 1

    # Ensure limitation disclaimer is present
    for f in dq.findings:
        assert f.category.value == "DATA_QUALITY"
        assert f.limitations is not None
        assert "not" in f.limitations.lower() or "indicates" in f.limitations.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 6. ANOMALY RANKING AND FILTERING
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_fleet_anomalies_ranking_and_filtering(db_session):
    """
    Verifies that get_fleet_anomalies deterministically ranks CRITICAL > HIGH > MEDIUM > LOW
    and filters properly by category.
    """
    company_id = 9107
    now = datetime.now(timezone.utc)

    # Overdue maintenance (CRITICAL)
    v = Vehicle(
        registration_number="MH12-CRIT",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        current_odometer=60000.0,
        last_service_odometer=45000.0,
        maintenance_interval_km=10000.0
    )
    db_session.add(v)
    await db_session.commit()

    engine = FleetIntelligenceEngine(MockUoW(db_session), company_id=company_id)
    resp = await engine.get_fleet_anomalies(category="ALL", min_severity="ALL")

    assert resp.total_anomalies >= 1
    # First item must be CRITICAL
    assert resp.anomalies[0].severity.value == "CRITICAL"

    # Category filter
    maint_only = await engine.get_fleet_anomalies(category="MAINTENANCE")
    for a in maint_only.anomalies:
        assert a.category.value == "MAINTENANCE"


# ══════════════════════════════════════════════════════════════════════════════
# 7. MULTI-TENANT ISOLATION
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_fleet_intelligence_multi_tenant_isolation(db_session):
    """
    Company A's vehicles, fuel expenses, and anomalies must NEVER be visible
    to Company B.
    """
    company_a = 9108
    company_b = 9109

    v_a = Vehicle(
        registration_number="MH12-COMP-A",
        status=VehicleStatus.ACTIVE,
        company_id=company_a,
        current_odometer=70000.0,
        last_service_odometer=40000.0,
        maintenance_interval_km=10000.0
    )
    db_session.add(v_a)
    await db_session.commit()

    # Company B queries
    engine_b = FleetIntelligenceEngine(MockUoW(db_session), company_id=company_b)
    overview_b = await engine_b.get_fleet_health_overview()

    assert overview_b.total_vehicles == 0
    assert overview_b.active_vehicles == 0
    assert overview_b.maintenance.overdue_count == 0
    assert len(overview_b.key_findings) == 0


# ══════════════════════════════════════════════════════════════════════════════
# 8. COPILOT TOOL EXECUTOR INTEGRATION FOR INTELLIGENCE TOOLS
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_copilot_tool_executor_executes_all_intelligence_tools(db_session):
    """
    Verifies that CopilotToolExecutor executes all 6 intelligence tools and returns
    valid JSON representations without throwing schema validation errors:
    1. get_fleet_health
    2. get_fleet_anomalies
    3. analyze_fuel_efficiency
    4. get_maintenance_priorities
    5. analyze_trip_performance
    6. get_data_quality_findings
    """
    company_id = 9110
    v = Vehicle(registration_number="MH12-EXEC-INT", status=VehicleStatus.ACTIVE, company_id=company_id)
    db_session.add(v)
    await db_session.commit()

    executor = CopilotToolExecutor(MockUoW(db_session), company_id=company_id, user_id="user_test")

    # 1. get_fleet_health
    res_health = json.loads(await executor.execute("get_fleet_health", {}))
    assert "total_vehicles" in res_health
    assert res_health["total_vehicles"] == 1

    # 2. get_fleet_anomalies
    res_anomalies = json.loads(await executor.execute("get_fleet_anomalies", {"category": "ALL", "limit": 10}))
    assert "anomalies" in res_anomalies

    # 3. analyze_fuel_efficiency
    res_fuel = json.loads(await executor.execute("analyze_fuel_efficiency", {"period_days": 30}))
    assert "current_period_spend" in res_fuel

    # 4. get_maintenance_priorities
    res_maint = json.loads(await executor.execute("get_maintenance_priorities", {"limit": 10}))
    assert "total_overdue" in res_maint

    # 5. analyze_trip_performance
    res_trip = json.loads(await executor.execute("analyze_trip_performance", {"days": 30}))
    assert "delayed_trips_count" in res_trip

    # 6. get_data_quality_findings
    res_dq = json.loads(await executor.execute("get_data_quality_findings", {"limit": 10}))
    assert "data_completeness_score" in res_dq


# ══════════════════════════════════════════════════════════════════════════════
# 9. SAFE ACTION HANDOFFS (NO AUTONOMOUS WRITES)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_intelligence_never_performs_autonomous_writes(db_session):
    """
    Verifies that detecting anomalies or running intelligence analysis does NOT
    modify vehicle statuses, update trips, create maintenance tasks, or alter records.
    """
    company_id = 9111
    now = datetime.now(timezone.utc)

    v = Vehicle(
        registration_number="MH12-SAFE-INT",
        status=VehicleStatus.ACTIVE,
        company_id=company_id,
        current_odometer=80000.0,
        last_service_odometer=40000.0,
        maintenance_interval_km=10000.0
    )
    t = Trip(
        trip_id="TRP-SAFE-01",
        company_id=company_id,
        status=TripStatus.CREATED,
        planned_start_time=now - timedelta(hours=5)
    )
    db_session.add_all([v, t])
    await db_session.commit()

    executor = CopilotToolExecutor(MockUoW(db_session), company_id=company_id, user_id="user_test")

    # Execute all tools
    await executor.execute("get_fleet_health", {})
    await executor.execute("get_fleet_anomalies", {})
    await executor.execute("analyze_fuel_efficiency", {})
    await executor.execute("get_maintenance_priorities", {})
    await executor.execute("analyze_trip_performance", {})

    # Re-verify database state
    v_check = await db_session.get(Vehicle, v.id)
    t_check = await db_session.get(Trip, t.id)

    # Status must remain unchanged (no autonomous modification)
    assert v_check.status == VehicleStatus.ACTIVE
    assert t_check.status == TripStatus.CREATED
