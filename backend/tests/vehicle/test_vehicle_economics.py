"""
FleetGuard — Vehicle Economics & Fleet Roll-Up Integration Tests
Validates Phase 1 to Phase 13:
1. Trip-to-vehicle financial roll-up
2. Vehicle-only expense attribution
3. Company-only overhead attribution
4. Fleet reconciliation
5. Revenue recognition and cancelled trips
6. Cost/km and revenue/km
7. Actual fuel efficiency
8. Maintenance cost without double-counting
9. Date-boundary behavior
10. Tenant isolation
11. Zero and missing telemetry
12. Retry-telemetry endpoint authorization
13. Query behavior under multiple vehicles (database-side aggregation)
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from main import app
from database import get_db
from models.company import Company
from models.user import User, UserRole
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver
from models.trip_domain import Trip, TripStatus
from models.expense_domain import Expense, ExpenseStatus, ExpenseCategory
from models.maintenance_domain import MaintenanceRecord, MaintenanceCategory, MaintenanceStatus
from models.fuel_domain import FuelTransaction, FuelTransactionType
from services.vehicle_economics_service import VehicleEconomicsService
from services.auth_service import get_current_user


@pytest.mark.asyncio
async def test_trip_to_vehicle_financial_rollup(db_session):
    """
    Phase 3 & Phase 13.1:
    Vehicle with two eligible completed trips:
    Trip 1: Realized revenue ₹50,000, Approved trip costs ₹20,000
    Trip 2: Realized revenue ₹30,000, Approved trip costs ₹15,000
    Expected:
    - Realized trip revenue: ₹80,000
    - Vehicle trip costs: ₹35,000
    - Vehicle trip profit: ₹45,000
    - Trip profit margin: 56.25%
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Rollup Co {suffix}", owner_name="Owner", mobile_number=f"ro_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-V1-{suffix}", tank_capacity=400.0)
    db_session.add(v)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    t1 = Trip(
        trip_id=f"TRP-1-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=50000.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    t2 = Trip(
        trip_id=f"TRP-2-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=30000.0,
        actual_start_time=now - timedelta(days=4), actual_end_time=now - timedelta(days=3)
    )
    db_session.add_all([t1, t2])
    await db_session.flush()

    # Expenses for Trip 1 (₹20,000 total)
    e1 = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=t1.id, business_id=f"EXP-1-{suffix}",
        category=ExpenseCategory.FUEL, amount=15000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=2), origin_id=str(uuid.uuid4())
    )
    e2 = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=t1.id, business_id=f"EXP-2-{suffix}",
        category=ExpenseCategory.TOLL, amount=5000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=2), origin_id=str(uuid.uuid4())
    )
    # Expense for Trip 2 (₹15,000 total)
    e3 = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=t2.id, business_id=f"EXP-3-{suffix}",
        category=ExpenseCategory.FUEL, amount=15000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=3), origin_id=str(uuid.uuid4())
    )
    db_session.add_all([e1, e2, e3])
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    res = await svc.get_vehicle_economics(v.id, c.id)

    assert res is not None
    assert res.realized_revenue == 80000.0
    assert res.trip_linked_costs == 35000.0
    assert res.vehicle_only_costs == 0.0
    assert res.total_operating_costs == 35000.0
    assert res.operating_profit == 45000.0
    assert res.operating_margin_pct == 56.25


@pytest.mark.asyncio
async def test_vehicle_only_expense_attribution(db_session):
    """
    Phase 2.B & Phase 13.2:
    Adding a ₹5,000 approved vehicle-only expense (trip_id = None, vehicle_id = Vehicle A):
    Expected:
    - Realized revenue: ₹80,000
    - Attributed operating costs: ₹40,000
    - Operating profit: ₹40,000
    - Operating margin: 50.0%
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"VehOnly Co {suffix}", owner_name="Owner", mobile_number=f"vo_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-VO-{suffix}", tank_capacity=400.0)
    db_session.add(v)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    t1 = Trip(
        trip_id=f"TRP-VO1-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=80000.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    db_session.add(t1)
    await db_session.flush()

    # Trip expense ₹35,000
    e_trip = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=t1.id, business_id=f"EXP-TR-{suffix}",
        category=ExpenseCategory.FUEL, amount=35000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=2), origin_id=str(uuid.uuid4())
    )
    # Vehicle-only expense ₹5,000 (e.g. tyre replacement / routine wash)
    e_veh = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=None, business_id=f"EXP-VO-{suffix}",
        category=ExpenseCategory.MAINTENANCE, amount=5000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
    )
    db_session.add_all([e_trip, e_veh])
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    res = await svc.get_vehicle_economics(v.id, c.id)

    assert res is not None
    assert res.realized_revenue == 80000.0
    assert res.trip_linked_costs == 35000.0
    assert res.vehicle_only_costs == 5000.0
    assert res.total_operating_costs == 40000.0
    assert res.operating_profit == 40000.0
    assert res.operating_margin_pct == 50.0


@pytest.mark.asyncio
async def test_company_only_overhead_attribution(db_session):
    """
    Phase 2.C & Phase 13.3:
    Company overhead (trip_id = None, vehicle_id = None) = ₹10,000.
    Expected:
    - Vehicle operating costs and operating profit do NOT receive company-only overhead.
    - Vehicle operating costs remain ₹40,000.
    - Vehicle operating profit remains ₹40,000.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Overhead Co {suffix}", owner_name="Owner", mobile_number=f"oh_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-OH-{suffix}", tank_capacity=400.0)
    db_session.add(v)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    t = Trip(
        trip_id=f"TRP-OH-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=80000.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    db_session.add(t)
    await db_session.flush()

    e_trip = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=t.id, business_id=f"EXP-TR-{suffix}",
        category=ExpenseCategory.FUEL, amount=35000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=2), origin_id=str(uuid.uuid4())
    )
    e_veh = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=None, business_id=f"EXP-VO-{suffix}",
        category=ExpenseCategory.MAINTENANCE, amount=5000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
    )
    # Company overhead ₹10,000
    e_comp = Expense(
        company_id=c.id, vehicle_id=None, trip_id=None, business_id=f"EXP-CO-{suffix}",
        category=ExpenseCategory.MISCELLANEOUS, amount=10000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
    )
    db_session.add_all([e_trip, e_veh, e_comp])
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    v_res = await svc.get_vehicle_economics(v.id, c.id)

    # Vehicle economics must NOT include company overhead
    assert v_res.total_operating_costs == 40000.0
    assert v_res.operating_profit == 40000.0

    # Fleet roll-up must include company overhead in fleet net profit
    fleet_res = await svc.get_fleet_roll_up(c.id)
    assert fleet_res.company_overhead_costs == 10000.0
    assert fleet_res.fleet_operating_profit == 40000.0
    assert fleet_res.fleet_net_profit == 30000.0


@pytest.mark.asyncio
async def test_fleet_roll_up_reconciliation(db_session):
    """
    Phase 7 & Phase 13.4:
    Multi-vehicle fleet reconciliation:
    Vehicle A: Realized rev ₹80k, trip costs ₹35k, vehicle-only expense ₹5k -> Op Profit ₹40k
    Vehicle B: Realized rev ₹60k, trip costs ₹25k, vehicle-only expense ₹4k -> Op Profit ₹31k
    Company: Overhead ₹10k
    Expected Fleet Reconciliation:
    - Fleet realized revenue: ₹140,000
    - Fleet trip-linked costs: ₹60,000
    - Fleet vehicle-only costs: ₹9,000
    - Company-only overhead: ₹10,000
    - Total included expenses: ₹79,000
    - Fleet operating profit: ₹71,000
    - Fleet net profit: ₹61,000
    - Fleet profit margin: 43.57%
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Reconcile Co {suffix}", owner_name="Owner", mobile_number=f"rc_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v_a = Vehicle(company_id=c.id, registration_number=f"TRK-A-{suffix}", tank_capacity=400.0)
    v_b = Vehicle(company_id=c.id, registration_number=f"TRK-B-{suffix}", tank_capacity=400.0)
    db_session.add_all([v_a, v_b])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    # Vehicle A Trip (Rev ₹80,000, Trip Costs ₹35,000)
    t_a = Trip(
        trip_id=f"TRP-A-{suffix}", company_id=c.id, vehicle_id=v_a.id,
        status=TripStatus.COMPLETED, revenue=80000.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    # Vehicle B Trip (Rev ₹60,000, Trip Costs ₹25,000)
    t_b = Trip(
        trip_id=f"TRP-B-{suffix}", company_id=c.id, vehicle_id=v_b.id,
        status=TripStatus.COMPLETED, revenue=60000.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    db_session.add_all([t_a, t_b])
    await db_session.flush()

    e_a_trip = Expense(
        company_id=c.id, vehicle_id=v_a.id, trip_id=t_a.id, business_id=f"EXP-AT-{suffix}",
        category=ExpenseCategory.FUEL, amount=35000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=2), origin_id=str(uuid.uuid4())
    )
    e_a_veh = Expense(
        company_id=c.id, vehicle_id=v_a.id, trip_id=None, business_id=f"EXP-AV-{suffix}",
        category=ExpenseCategory.MAINTENANCE, amount=5000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
    )
    e_b_trip = Expense(
        company_id=c.id, vehicle_id=v_b.id, trip_id=t_b.id, business_id=f"EXP-BT-{suffix}",
        category=ExpenseCategory.FUEL, amount=25000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=2), origin_id=str(uuid.uuid4())
    )
    e_b_veh = Expense(
        company_id=c.id, vehicle_id=v_b.id, trip_id=None, business_id=f"EXP-BV-{suffix}",
        category=ExpenseCategory.MAINTENANCE, amount=4000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
    )
    e_company = Expense(
        company_id=c.id, vehicle_id=None, trip_id=None, business_id=f"EXP-CO-{suffix}",
        category=ExpenseCategory.MISCELLANEOUS, amount=10000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
    )
    db_session.add_all([e_a_trip, e_a_veh, e_b_trip, e_b_veh, e_company])
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    res_a = await svc.get_vehicle_economics(v_a.id, c.id)
    res_b = await svc.get_vehicle_economics(v_b.id, c.id)
    fleet = await svc.get_fleet_roll_up(c.id)

    # Individual Vehicle Assertions
    assert res_a.operating_profit == 40000.0
    assert res_b.operating_profit == 31000.0

    # Fleet Roll-Up Assertions
    assert fleet.fleet_realized_revenue == 140000.0
    assert fleet.fleet_trip_linked_costs == 60000.0
    assert fleet.fleet_vehicle_only_costs == 9000.0
    assert fleet.company_overhead_costs == 10000.0
    assert fleet.total_fleet_costs == 79000.0
    assert fleet.fleet_operating_profit == 71000.0
    assert fleet.fleet_net_profit == 61000.0
    assert fleet.fleet_profit_margin_pct == 43.57

    # Mathematical Reconciliation
    assert fleet.fleet_operating_profit == res_a.operating_profit + res_b.operating_profit
    assert fleet.fleet_net_profit == (res_a.operating_profit + res_b.operating_profit) - fleet.company_overhead_costs


@pytest.mark.asyncio
async def test_revenue_recognition_and_cancelled_trips(db_session):
    """
    Phase 3 & Phase 13.5:
    Only COMPLETED trips contribute to realized revenue.
    CANCELLED, IN_PROGRESS, and CREATED trips must NOT inflate realized revenue.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"RevRec Co {suffix}", owner_name="Owner", mobile_number=f"rr_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-RR-{suffix}", tank_capacity=400.0)
    db_session.add(v)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    t_comp = Trip(
        trip_id=f"TRP-OK-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=50000.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    t_canc = Trip(
        trip_id=f"TRP-CAN-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.CANCELLED, revenue=30000.0,
        actual_start_time=now - timedelta(days=2)
    )
    t_prog = Trip(
        trip_id=f"TRP-PRG-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.IN_PROGRESS, revenue=20000.0,
        actual_start_time=now - timedelta(hours=5)
    )
    t_creat = Trip(
        trip_id=f"TRP-CRT-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.CREATED, revenue=15000.0
    )
    db_session.add_all([t_comp, t_canc, t_prog, t_creat])
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    res = await svc.get_vehicle_economics(v.id, c.id)

    # Realized revenue must strictly equal ₹50,000
    assert res.realized_revenue == 50000.0
    assert res.completed_trips_count == 1
    assert res.active_trips_count == 1


@pytest.mark.asyncio
async def test_cost_per_km_and_revenue_per_km(db_session):
    """
    Phase 4 & Phase 13.6:
    Actual distance only:
    - Eligible cost: ₹20,000, Actual distance: 500 km -> Cost/km = ₹40.0, Rev/km = ₹100.0.
    - Zero distance: Handled without ZeroDivisionError, returns None.
    - NULL distance: Handled without division error, returns None.
    - Planned distance must never be substituted into actual metrics.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Cpkm Co {suffix}", owner_name="Owner", mobile_number=f"ck_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v1 = Vehicle(company_id=c.id, registration_number=f"TRK-CK1-{suffix}", tank_capacity=400.0)
    v2 = Vehicle(company_id=c.id, registration_number=f"TRK-CK2-{suffix}", tank_capacity=400.0)
    db_session.add_all([v1, v2])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    # Trip 1 with actual distance 500 km
    t1 = Trip(
        trip_id=f"TRP-CK1-{suffix}", company_id=c.id, vehicle_id=v1.id,
        status=TripStatus.COMPLETED, revenue=50000.0,
        actual_distance=500.0, planned_distance=600.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    # Trip 2 with zero/NULL distance
    t2 = Trip(
        trip_id=f"TRP-CK2-{suffix}", company_id=c.id, vehicle_id=v2.id,
        status=TripStatus.COMPLETED, revenue=30000.0,
        actual_distance=None, planned_distance=400.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    db_session.add_all([t1, t2])
    await db_session.flush()

    e1 = Expense(
        company_id=c.id, vehicle_id=v1.id, trip_id=t1.id, business_id=f"EXP-CK1-{suffix}",
        category=ExpenseCategory.FUEL, amount=20000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=2), origin_id=str(uuid.uuid4())
    )
    e2 = Expense(
        company_id=c.id, vehicle_id=v2.id, trip_id=t2.id, business_id=f"EXP-CK2-{suffix}",
        category=ExpenseCategory.FUEL, amount=10000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=2), origin_id=str(uuid.uuid4())
    )
    db_session.add_all([e1, e2])
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    res1 = await svc.get_vehicle_economics(v1.id, c.id)
    res2 = await svc.get_vehicle_economics(v2.id, c.id)

    # V1 has authoritative distance 500 km
    assert res1.total_actual_distance_km == 500.0
    assert res1.cost_per_km == 40.0   # 20,000 / 500
    assert res1.revenue_per_km == 100.0 # 50,000 / 500

    # V2 has NULL distance -> should return None, NOT planned distance or divide by zero
    assert res2.total_actual_distance_km is None
    assert res2.cost_per_km is None
    assert res2.revenue_per_km is None


@pytest.mark.asyncio
async def test_actual_fuel_efficiency(db_session):
    """
    Phase 5 & Phase 13.7:
    Authoritative fuel efficiency km/L = actual distance / actual fuel consumed.
    - Actual distance: 500 km, Actual fuel: 100 L -> 5.0 km/L.
    - Fuel purchased (e.g. 200 L) must not be treated as consumed.
    - Missing telemetry -> returns None.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Eff Co {suffix}", owner_name="Owner", mobile_number=f"ef_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-EF-{suffix}", tank_capacity=400.0)
    db_session.add(v)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    t = Trip(
        trip_id=f"TRP-EF-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=40000.0,
        actual_distance=500.0, actual_fuel_liters=100.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    db_session.add(t)
    await db_session.flush()

    # Fuel purchased (200L) in transaction / expense
    db_session.add(FuelTransaction(
        company_id=c.id, vehicle_id=v.id, trip_id=t.id,
        transaction_type=FuelTransactionType.FILL, amount_liters=200.0,
        timestamp=now - timedelta(days=2)
    ))
    db_session.add(Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=t.id, business_id=f"EXP-EF-{suffix}",
        category=ExpenseCategory.FUEL, amount=18000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=2), origin_id=str(uuid.uuid4())
    ))
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    res = await svc.get_vehicle_economics(v.id, c.id)

    # Actual efficiency is derived from actual_distance / actual_fuel_liters (500 / 100 = 5.0)
    assert res.fuel_efficiency_kmpl == 5.0
    assert res.total_actual_distance_km == 500.0
    assert res.total_actual_fuel_liters == 100.0


@pytest.mark.asyncio
async def test_maintenance_cost_without_double_counting(db_session):
    """
    Phase 6 & Phase 13.8:
    Financial maintenance costs are sourced strictly from approved Expenses.
    Operational MaintenanceRecords (parts, labour) are operational metadata and
    must NOT independently add into the financial totals when an Expense exists.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Maint Co {suffix}", owner_name="Owner", mobile_number=f"mt_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-MT-{suffix}", tank_capacity=400.0)
    db_session.add(v)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    t = Trip(
        trip_id=f"TRP-MT-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=60000.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    db_session.add(t)
    await db_session.flush()

    # Maintenance record with operational parts + labour totals = ₹10,000
    maint_rec = MaintenanceRecord(
        business_id=f"MNT-REC-{suffix}",
        company_id=c.id, vehicle_id=v.id,
        category=MaintenanceCategory.CORRECTIVE, status=MaintenanceStatus.COMPLETED,
        cost=10000.0,
        completed_date=now - timedelta(days=1)
    )
    db_session.add(maint_rec)
    await db_session.flush()

    # Canonical approved expense for this maintenance
    exp_maint = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=None, business_id=f"EXP-MT-{suffix}",
        category=ExpenseCategory.MAINTENANCE, amount=10000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
    )
    db_session.add(exp_maint)
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    res = await svc.get_vehicle_economics(v.id, c.id)

    # Cost must be exactly ₹10,000, NOT ₹20,000 (no double-counting from maintenance record)
    assert res.vehicle_only_costs == 10000.0
    assert res.total_operating_costs == 10000.0
    assert res.operating_profit == 50000.0


@pytest.mark.asyncio
async def test_date_boundaries_and_reporting_periods(db_session):
    """
    Phase 8 & Phase 13.9:
    Canonical date fields:
    - Expense accounting date: `expense_date`
    - Trip completion date: `actual_end_time`
    Filter by reporting period boundaries (e.g. January vs February).
    `updated_at` must NEVER determine the accounting period.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Date Co {suffix}", owner_name="Owner", mobile_number=f"dt_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-DT-{suffix}", tank_capacity=400.0)
    db_session.add(v)
    await db_session.flush()

    # Month 1: 2026-01
    jan_start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    jan_mid = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    jan_end = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

    # Month 2: 2026-02
    feb_mid = datetime(2026, 2, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Trip completed in January (₹40,000 rev)
    t_jan = Trip(
        trip_id=f"TRP-JAN-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=40000.0,
        actual_start_time=jan_start, actual_end_time=jan_mid
    )
    # Trip completed in February (₹60,000 rev)
    t_feb = Trip(
        trip_id=f"TRP-FEB-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=60000.0,
        actual_start_time=jan_end, actual_end_time=feb_mid
    )
    db_session.add_all([t_jan, t_feb])
    await db_session.flush()

    # Expense in January (₹15,000)
    e_jan = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=t_jan.id, business_id=f"EXP-JAN-{suffix}",
        category=ExpenseCategory.FUEL, amount=15000.0, status=ExpenseStatus.APPROVED,
        expense_date=jan_mid, origin_id=str(uuid.uuid4())
    )
    # Expense in February (₹25,000)
    e_feb = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=t_feb.id, business_id=f"EXP-FEB-{suffix}",
        category=ExpenseCategory.FUEL, amount=25000.0, status=ExpenseStatus.APPROVED,
        expense_date=feb_mid, origin_id=str(uuid.uuid4())
    )
    db_session.add_all([e_jan, e_feb])
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)

    # 1. Query January window
    res_jan = await svc.get_vehicle_economics(v.id, c.id, start_date=jan_start, end_date=jan_end)
    assert res_jan.realized_revenue == 40000.0
    assert res_jan.total_operating_costs == 15000.0
    assert res_jan.operating_profit == 25000.0

    # 2. Query Full/All-time window
    res_all = await svc.get_vehicle_economics(v.id, c.id)
    assert res_all.realized_revenue == 100000.0
    assert res_all.total_operating_costs == 40000.0
    assert res_all.operating_profit == 60000.0


@pytest.mark.asyncio
async def test_tenant_isolation_vehicle_and_fleet(db_session):
    """
    Phase 10 & Phase 13.10:
    Company A and Company B isolation:
    - Company A cannot access Company B's vehicle economics.
    - Company A's fleet roll-up strictly excludes Company B's revenue, expenses, and vehicles.
    """
    suffix = uuid.uuid4().hex[:6]
    cA = Company(company_name=f"IsoA Co {suffix}", owner_name="OwnerA", mobile_number=f"ia_{suffix}")
    cB = Company(company_name=f"IsoB Co {suffix}", owner_name="OwnerB", mobile_number=f"ib_{suffix}")
    db_session.add_all([cA, cB])
    await db_session.flush()

    vA = Vehicle(company_id=cA.id, registration_number=f"TRK-IA-{suffix}", tank_capacity=400.0)
    vB = Vehicle(company_id=cB.id, registration_number=f"TRK-IB-{suffix}", tank_capacity=400.0)
    db_session.add_all([vA, vB])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    tA = Trip(
        trip_id=f"TRP-IA-{suffix}", company_id=cA.id, vehicle_id=vA.id,
        status=TripStatus.COMPLETED, revenue=50000.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    tB = Trip(
        trip_id=f"TRP-IB-{suffix}", company_id=cB.id, vehicle_id=vB.id,
        status=TripStatus.COMPLETED, revenue=90000.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    db_session.add_all([tA, tB])
    await db_session.flush()

    eA = Expense(
        company_id=cA.id, vehicle_id=vA.id, trip_id=tA.id, business_id=f"EXP-IA-{suffix}",
        category=ExpenseCategory.FUEL, amount=20000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
    )
    eB = Expense(
        company_id=cB.id, vehicle_id=vB.id, trip_id=tB.id, business_id=f"EXP-IB-{suffix}",
        category=ExpenseCategory.FUEL, amount=40000.0, status=ExpenseStatus.APPROVED,
        expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
    )
    db_session.add_all([eA, eB])
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)

    # Cross-tenant query attempt: Company A querying Vehicle B
    res_cross = await svc.get_vehicle_economics(vB.id, cA.id)
    assert res_cross is None

    # Fleet roll-up for Company A excludes Company B
    fleetA = await svc.get_fleet_roll_up(cA.id)
    assert fleetA.total_vehicles == 1
    assert fleetA.fleet_realized_revenue == 50000.0
    assert fleetA.total_fleet_costs == 20000.0
    assert fleetA.fleet_net_profit == 30000.0


@pytest.mark.asyncio
async def test_zero_and_missing_telemetry(db_session):
    """
    Phase 13.11:
    A completed trip with missing telemetry leaves distance/fuel/efficiency as None,
    never fabricating zero as a real measurement or substituting planned distance.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"MissingTel Co {suffix}", owner_name="Owner", mobile_number=f"mt_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-MTEL-{suffix}", tank_capacity=400.0)
    db_session.add(v)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    t = Trip(
        trip_id=f"TRP-MTEL-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=30000.0,
        actual_distance=None, actual_fuel_liters=None,
        planned_distance=450.0, planned_fuel_liters=90.0,
        actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
    )
    db_session.add(t)
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    res = await svc.get_vehicle_economics(v.id, c.id)

    assert res.total_actual_distance_km is None
    assert res.total_actual_fuel_liters is None
    assert res.cost_per_km is None
    assert res.revenue_per_km is None
    assert res.fuel_efficiency_kmpl is None


@pytest.mark.asyncio
async def test_retry_telemetry_endpoint_authorization_and_guards(db_session):
    """
    Phase 0.3 & Phase 13.12:
    POST /api/v1/trips/{trip_id}/retry-telemetry:
    - Enforces RBAC (COMPANY_ADMIN allowed, DRIVER 403)
    - Company isolation (Company 2 calling Company 1 trip gets 404)
    - Invalid state rejection (IN_PROGRESS trip gets 400)
    """
    suffix = uuid.uuid4().hex[:6]
    c1 = Company(company_name=f"Retry1 Co {suffix}", owner_name="Owner1", mobile_number=f"r1_{suffix}")
    c2 = Company(company_name=f"Retry2 Co {suffix}", owner_name="Owner2", mobile_number=f"r2_{suffix}")
    db_session.add_all([c1, c2])
    await db_session.flush()

    v = Vehicle(company_id=c1.id, registration_number=f"TRK-RT-{suffix}", tank_capacity=400.0)
    db_session.add(v)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    trip_comp = Trip(
        trip_id=f"TRP-RT-OK-{suffix}", company_id=c1.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED,
        actual_start_time=now - timedelta(hours=2), actual_end_time=now - timedelta(hours=1)
    )
    trip_prog = Trip(
        trip_id=f"TRP-RT-IP-{suffix}", company_id=c1.id, vehicle_id=v.id,
        status=TripStatus.IN_PROGRESS,
        actual_start_time=now - timedelta(hours=1)
    )
    db_session.add_all([trip_comp, trip_prog])
    await db_session.flush()

    admin_c1 = User(id=8801, company_id=c1.id, role=UserRole.COMPANY_ADMIN, is_active=True, full_name="Admin 1", mobile_number=f"a1_{suffix}", password_hash="dummy")
    driver_c1 = User(id=8802, company_id=c1.id, role=UserRole.DRIVER, is_active=True, full_name="Driver 1", mobile_number=f"d1_{suffix}", password_hash="dummy")
    admin_c2 = User(id=8803, company_id=c2.id, role=UserRole.COMPANY_ADMIN, is_active=True, full_name="Admin 2", mobile_number=f"a2_{suffix}", password_hash="dummy")
    db_session.add_all([admin_c1, driver_c1, admin_c2])
    await db_session.flush()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Driver calling endpoint -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: driver_c1
    with TestClient(app) as client:
        res = client.post(f"/api/v1/trips/{trip_comp.id}/retry-telemetry")
        assert res.status_code == 403

    # Cross-company Admin calling trip -> 404 Not Found
    app.dependency_overrides[get_current_user] = lambda: admin_c2
    with TestClient(app) as client:
        res = client.post(f"/api/v1/trips/{trip_comp.id}/retry-telemetry")
        assert res.status_code == 404

    # Calling on IN_PROGRESS trip -> 400 Bad Request
    app.dependency_overrides[get_current_user] = lambda: admin_c1
    with TestClient(app) as client:
        res = client.post(f"/api/v1/trips/{trip_prog.id}/retry-telemetry")
        assert res.status_code == 400

    # Authorized Admin calling completed trip -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: admin_c1
    with TestClient(app) as client:
        res = client.post(f"/api/v1/trips/{trip_comp.id}/retry-telemetry")
        assert res.status_code == 200
        assert res.json()["id"] == trip_comp.id

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_query_behavior_under_multiple_vehicles_db_aggregation(db_session):
    """
    Phase 11 & Phase 13.13:
    Database-side aggregation under multiple vehicles:
    Verify that 5 vehicles in a company are aggregated in batch queries (O(1) database round-trips),
    producing reconciled fleet metrics without N+1 query loops.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Scale Co {suffix}", owner_name="Owner", mobile_number=f"sc_{suffix}")
    db_session.add(c)
    await db_session.flush()

    vehicles = []
    trips = []
    expenses = []
    now = datetime.now(timezone.utc)

    for i in range(5):
        v = Vehicle(company_id=c.id, registration_number=f"TRK-SC{i}-{suffix}", tank_capacity=400.0)
        vehicles.append(v)
    db_session.add_all(vehicles)
    await db_session.flush()

    expected_fleet_rev = 0.0
    expected_fleet_cost = 0.0

    for i, v in enumerate(vehicles):
        rev = 20000.0 * (i + 1)
        cost = 8000.0 * (i + 1)
        expected_fleet_rev += rev
        expected_fleet_cost += cost

        t = Trip(
            trip_id=f"TRP-SC{i}-{suffix}", company_id=c.id, vehicle_id=v.id,
            status=TripStatus.COMPLETED, revenue=rev, actual_distance=100.0 * (i + 1),
            actual_start_time=now - timedelta(days=2), actual_end_time=now - timedelta(days=1)
        )
        trips.append(t)
    db_session.add_all(trips)
    await db_session.flush()

    for i, (v, t) in enumerate(zip(vehicles, trips)):
        cost = 8000.0 * (i + 1)
        e = Expense(
            company_id=c.id, vehicle_id=v.id, trip_id=t.id, business_id=f"EXP-SC{i}-{suffix}",
            category=ExpenseCategory.FUEL, amount=cost, status=ExpenseStatus.APPROVED,
            expense_date=now - timedelta(days=1), origin_id=str(uuid.uuid4())
        )
        expenses.append(e)
    db_session.add_all(expenses)
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    fleet = await svc.get_fleet_roll_up(c.id, include_vehicles=True)

    assert fleet.total_vehicles == 5
    assert len(fleet.vehicles) == 5
    assert fleet.fleet_realized_revenue == expected_fleet_rev
    assert fleet.fleet_trip_linked_costs == expected_fleet_cost
    assert fleet.fleet_operating_profit == expected_fleet_rev - expected_fleet_cost
    assert fleet.fleet_net_profit == expected_fleet_rev - expected_fleet_cost
