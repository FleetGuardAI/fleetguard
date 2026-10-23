"""
FleetGuard — Final FIE Technical Debt Closure Verification Test Suite
Validates:
1. Unbounded vs Bounded Utilization Semantics (empty fleet, idle vehicle, completed trips, missing timestamps, active trips).
2. Financial Reporting-Period Reconciliation across Month Boundaries (Sept expense vs Oct trip completion, zero duplication).
3. Sweeper Coordination Requirements (concurrent workers, lock acquisition, duplicate prevention, lock release on failure).
4. Auto-inheritance of vehicle_id for trip-linked expenses.
"""

import uuid
import asyncio
from datetime import datetime, timezone, timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.company import Company
from models.vehicle_domain import Vehicle, VehicleStatus
from models.trip_domain import Trip, TripStatus
from models.expense_domain import Expense, ExpenseStatus, ExpenseCategory
from services.vehicle_economics_service import VehicleEconomicsService
from services.trip_intelligence_service import TripIntelligenceService
from infrastructure.uow import AbstractUnitOfWork
from infrastructure.intelligence.sweeper_worker import IntelligenceSweeperWorker, DistributedSweeperLock


@pytest.mark.asyncio
async def test_unbounded_vs_bounded_utilization_semantics(db_session):
    """
    Section 1: Verify utilization semantics:
    - Bounded window calculates actual elapsed-time utilization intersecting the window.
    - Unbounded window sets utilization_rate_pct = None and exposes activity_score.
    - Missing timestamps safely yield utilization_rate_pct = None without fabrication.
    - Idle vehicle yields utilization_rate_pct = 0.0 in bounded window, activity_score = 0.0 in unbounded.
    - Empty fleet yields None for both.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Util Co {suffix}", owner_name="Owner", mobile_number=f"ut_{suffix}")
    db_session.add(c)
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)

    # 1. Empty fleet
    fleet_empty = await svc.get_fleet_roll_up(c.id)
    assert fleet_empty.total_vehicles == 0
    assert fleet_empty.fleet_utilization_rate_pct is None
    assert fleet_empty.fleet_activity_score is None

    # 2. Add 4 vehicles:
    # v_idle: 0 trips
    # v_active: 1 in-progress trip
    # v_timed: 2 completed trips with valid timestamps (total 24 hours in a 48 hour window)
    # v_untimed: 1 completed trip with NULL start/end timestamps
    v_idle = Vehicle(company_id=c.id, registration_number=f"IDLE-{suffix}")
    v_active = Vehicle(company_id=c.id, registration_number=f"ACT-{suffix}", status=VehicleStatus.ACTIVE)
    v_timed = Vehicle(company_id=c.id, registration_number=f"TIME-{suffix}", status=VehicleStatus.ACTIVE)
    v_untimed = Vehicle(company_id=c.id, registration_number=f"NOTIME-{suffix}", status=VehicleStatus.ACTIVE)
    db_session.add_all([v_idle, v_active, v_timed, v_untimed])
    await db_session.flush()

    # Active trip
    t_active = Trip(
        trip_id=f"TRP-ACT-{suffix}", company_id=c.id, vehicle_id=v_active.id,
        status=TripStatus.IN_PROGRESS, actual_start_time=datetime(2026, 10, 10, 8, 0, tzinfo=timezone.utc)
    )

    # Bounded window: 2026-10-10 00:00:00 to 2026-10-12 00:00:00 (48 hours = 172,800 seconds)
    window_start = datetime(2026, 10, 10, 0, 0, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 10, 12, 0, 0, 0, tzinfo=timezone.utc)

    # Timed vehicle trips:
    # Trip 1: 12 hours (Oct 10, 06:00 to 18:00)
    # Trip 2: 12 hours (Oct 11, 06:00 to 18:00)
    # Total = 24 hours out of 48 hours = exactly 50.0% utilization
    t_time1 = Trip(
        trip_id=f"TRP-T1-{suffix}", company_id=c.id, vehicle_id=v_timed.id,
        status=TripStatus.COMPLETED, revenue=30000.0,
        actual_start_time=datetime(2026, 10, 10, 6, 0, tzinfo=timezone.utc),
        actual_end_time=datetime(2026, 10, 10, 18, 0, tzinfo=timezone.utc),
        actual_distance=500.0, actual_fuel_liters=100.0
    )
    t_time2 = Trip(
        trip_id=f"TRP-T2-{suffix}", company_id=c.id, vehicle_id=v_timed.id,
        status=TripStatus.COMPLETED, revenue=30000.0,
        actual_start_time=datetime(2026, 10, 11, 6, 0, tzinfo=timezone.utc),
        actual_end_time=datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc),
        actual_distance=500.0, actual_fuel_liters=100.0
    )

    # Untimed vehicle trip: Completed, but missing timestamps
    t_untimed = Trip(
        trip_id=f"TRP-UT-{suffix}", company_id=c.id, vehicle_id=v_untimed.id,
        status=TripStatus.COMPLETED, revenue=20000.0,
        actual_start_time=None, actual_end_time=datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc),
        actual_distance=300.0, actual_fuel_liters=60.0
    )

    db_session.add_all([t_active, t_time1, t_time2, t_untimed])
    await db_session.flush()

    # --- Test Unbounded Window ---
    res_idle_unb = await svc.get_vehicle_economics(v_idle.id, c.id)
    assert res_idle_unb.utilization_rate_pct is None, "Unbounded window must not fabricate utilization_pct"
    assert res_idle_unb.activity_score == 0.0

    res_act_unb = await svc.get_vehicle_economics(v_active.id, c.id)
    assert res_act_unb.utilization_rate_pct is None, "Unbounded window must not expose trip-count heuristic as utilization_pct"
    assert res_act_unb.activity_score == 100.0, "Active trip vehicle should have activity_score 100.0"

    res_time_unb = await svc.get_vehicle_economics(v_timed.id, c.id)
    assert res_time_unb.utilization_rate_pct is None
    assert res_time_unb.activity_score == 20.0, "2 completed trips: min(100.0, 2 * 10.0) = 20.0 activity_score"

    fleet_unb = await svc.get_fleet_roll_up(c.id)
    assert fleet_unb.fleet_utilization_rate_pct is None, "Fleet unbounded must not expose utilization_pct"
    # Average activity: (0.0 + 100.0 + 20.0 + 10.0) / 4 = 130.0 / 4 = 32.5
    assert fleet_unb.fleet_activity_score == 32.5

    # --- Test Bounded Window ---
    res_idle_bnd = await svc.get_vehicle_economics(v_idle.id, c.id, start_date=window_start, end_date=window_end)
    assert res_idle_bnd.utilization_rate_pct == 0.0, "Idle vehicle in bounded window is 0.0% utilized"
    assert res_idle_bnd.activity_score is None

    res_time_bnd = await svc.get_vehicle_economics(v_timed.id, c.id, start_date=window_start, end_date=window_end)
    assert res_time_bnd.utilization_rate_pct == 50.0, "24 hours out of 48 hours window is exactly 50.0%"
    assert res_time_bnd.activity_score is None

    # Untimed vehicle has a completed trip in window but actual_start_time is None
    res_untimed_bnd = await svc.get_vehicle_economics(v_untimed.id, c.id, start_date=window_start, end_date=window_end)
    assert res_untimed_bnd.utilization_rate_pct is None, "Missing timestamps must NOT fabricate utilization"
    assert res_untimed_bnd.activity_score is None


@pytest.mark.asyncio
async def test_month_boundary_reporting_period_reconciliation(db_session):
    """
    Section 2: Reconcile financial reporting-period semantics.
    Scenario:
    - Trip starts on 2026-09-29, refuels on 2026-09-30 (expense dated in September ₹15,000).
    - Trip completes on 2026-10-02 (realized revenue ₹60,000).
    - Single vehicle unlinked maintenance expense in September: ₹5,000.
    - Company overhead expense in October: ₹10,000.

    Verify:
    - September Period (Sept 1 - Sept 30):
      Revenue = ₹0 (Trip completed in October)
      Trip-Linked Costs = ₹15,000 (expense_date in Sept)
      Vehicle-Only Costs = ₹5,000
      Total Operating Costs = ₹20,000
      Operating Profit = -₹20,000
    - October Period (Oct 1 - Oct 31):
      Revenue = ₹60,000 (Trip actual_end_time in Oct)
      Trip-Linked Costs = ₹0 (already accounted in Sept)
      Vehicle-Only Costs = ₹0
      Total Operating Costs = ₹0
      Operating Profit = ₹60,000
    - Combined Period (Sept 1 - Oct 31):
      Revenue = ₹60,000
      Trip-Linked Costs = ₹15,000
      Vehicle-Only Costs = ₹5,000
      Operating Profit = ₹40,000
      Company Overhead = ₹10,000
      Fleet Net Profit = ₹30,000
    - Trip Intelligence (Job-Costing matching):
      Trip Revenue = ₹60,000
      Approved Costs = ₹15,000
      Trip Net Profit = ₹45,000 (matches job costing lifecycle regardless of calendar boundary)
    - Zero duplication: The ₹15,000 fuel expense is recognized in September and NEVER duplicated in October.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"MonthBound Co {suffix}", owner_name="Owner", mobile_number=f"mb_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-MB-{suffix}")
    db_session.add(v)
    await db_session.flush()

    # Trip completed in October
    trip_completion_date = datetime(2026, 10, 2, 16, 0, tzinfo=timezone.utc)
    trip_start_date = datetime(2026, 9, 29, 8, 0, tzinfo=timezone.utc)

    t = Trip(
        trip_id=f"TRP-MB-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=60000.0,
        actual_start_time=trip_start_date, actual_end_time=trip_completion_date,
        actual_distance=800.0, actual_fuel_liters=180.0
    )
    db_session.add(t)
    await db_session.flush()

    # Trip fuel expense dated in September (Sept 30)
    exp_sept = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=t.id, business_id=f"EXP-S-{suffix}",
        category=ExpenseCategory.FUEL, amount=15000.0, status=ExpenseStatus.APPROVED,
        expense_date=datetime(2026, 9, 30, 14, 0, tzinfo=timezone.utc), origin_id=str(uuid.uuid4())
    )
    # Vehicle-only maintenance in September
    exp_veh_sept = Expense(
        company_id=c.id, vehicle_id=v.id, trip_id=None, business_id=f"EXP-VM-{suffix}",
        category=ExpenseCategory.MAINTENANCE, amount=5000.0, status=ExpenseStatus.APPROVED,
        expense_date=datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc), origin_id=str(uuid.uuid4())
    )
    # Company overhead in October
    exp_comp_oct = Expense(
        company_id=c.id, vehicle_id=None, trip_id=None, business_id=f"EXP-CO-{suffix}",
        category=ExpenseCategory.MISCELLANEOUS, amount=10000.0, status=ExpenseStatus.APPROVED,
        expense_date=datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc), origin_id=str(uuid.uuid4())
    )
    db_session.add_all([exp_sept, exp_veh_sept, exp_comp_oct])
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)

    sept_start = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    sept_end = datetime(2026, 9, 30, 23, 59, 59, tzinfo=timezone.utc)
    oct_start = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)
    oct_end = datetime(2026, 10, 31, 23, 59, 59, tzinfo=timezone.utc)

    # 1. September Accounting Period
    econ_sept = await svc.get_vehicle_economics(v.id, c.id, start_date=sept_start, end_date=sept_end)
    assert econ_sept.realized_revenue == 0.0, "Trip completed in October must not count towards September revenue"
    assert econ_sept.trip_linked_costs == 15000.0, "Fuel expense incurred on Sept 30 belongs to September ledger"
    assert econ_sept.vehicle_only_costs == 5000.0
    assert econ_sept.total_operating_costs == 20000.0
    assert econ_sept.operating_profit == -20000.0

    # 2. October Accounting Period
    econ_oct = await svc.get_vehicle_economics(v.id, c.id, start_date=oct_start, end_date=oct_end)
    assert econ_oct.realized_revenue == 60000.0, "Trip completed Oct 2 realizes revenue in October"
    assert econ_oct.trip_linked_costs == 0.0, "September fuel expense must NOT be duplicated in October"
    assert econ_oct.vehicle_only_costs == 0.0
    assert econ_oct.total_operating_costs == 0.0
    assert econ_oct.operating_profit == 60000.0

    # 3. Two-Month Combined Period
    econ_comb = await svc.get_vehicle_economics(v.id, c.id, start_date=sept_start, end_date=oct_end)
    assert econ_comb.realized_revenue == 60000.0
    assert econ_comb.trip_linked_costs == 15000.0
    assert econ_comb.vehicle_only_costs == 5000.0
    assert econ_comb.total_operating_costs == 20000.0
    assert econ_comb.operating_profit == 40000.0

    fleet_comb = await svc.get_fleet_roll_up(c.id, start_date=sept_start, end_date=oct_end)
    assert fleet_comb.fleet_realized_revenue == 60000.0
    assert fleet_comb.fleet_trip_linked_costs == 15000.0
    assert fleet_comb.fleet_vehicle_only_costs == 5000.0
    assert fleet_comb.company_overhead_costs == 10000.0
    assert fleet_comb.total_fleet_costs == 30000.0
    assert fleet_comb.fleet_operating_profit == 40000.0
    assert fleet_comb.fleet_net_profit == 30000.0

    # 4. Trip Intelligence (Job Costing)
    # Trip Intelligence groups by trip.id and matches all approved expenses to that trip
    class MockUOW(AbstractUnitOfWork):
        def __init__(self, session):
            self.session = session
            class MockRepos:
                class MockExpRepo:
                    async def get_expenses_by_trip(self_inner, trip_id):
                        return [exp_sept]
                expense = MockExpRepo()
            self.repositories = MockRepos()
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def commit(self): pass
        async def rollback(self): pass

    uow = MockUOW(db_session)
    ti_svc = TripIntelligenceService(uow)
    ti_resp = await ti_svc.compute_intelligence(t)
    assert ti_resp.financial_summary.revenue == 60000.0
    assert ti_resp.financial_summary.total_cost == 15000.0
    assert ti_resp.financial_summary.net_profit == 45000.0
    assert ti_resp.financial_summary.profit_margin_pct == 75.0


@pytest.mark.asyncio
async def test_sweeper_distributed_coordination(db_session):
    """
    Section 3: Verify sweeper coordination requirements.
    - Concurrent worker execution: second worker fails to acquire lock and skips gracefully.
    - Lock release on successful completion.
    - Lock release on worker failure / exception.
    """
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    class MockSessionFactory:
        async def __aenter__(self):
            return mock_session
        async def __aexit__(self, exc_type, exc_val, tb):
            pass

    worker1 = IntelligenceSweeperWorker(session_factory=lambda: MockSessionFactory())
    worker2 = IntelligenceSweeperWorker(session_factory=lambda: MockSessionFactory())

    # 1. Test lock acquisition and concurrent exclusion
    # Acquire lock in worker1 context manually to simulate long-running sweep
    async with DistributedSweeperLock(mock_session) as lock1:
        assert lock1.acquired is True

        # While lock1 is held, worker2 attempting a sweep must be denied
        did_sweep = await worker2._sweep_active_conditions()
        assert did_sweep is False, "Worker 2 must skip execution while Worker 1 holds the distributed lock"

    # Lock1 is now released
    # 2. Worker 2 can now acquire the lock and sweep successfully
    did_sweep_after = await worker2._sweep_active_conditions()
    assert did_sweep_after is True, "Worker 2 must acquire lock and execute once Worker 1 has released it"

    # 3. Test lock release on exception
    with patch("infrastructure.intelligence.sweeper_worker.MaintenanceDueService.sweep_maintenance_status", side_effect=RuntimeError("Simulated Failure")):
        with pytest.raises(RuntimeError, match="Simulated Failure"):
            await worker1._sweep_active_conditions()

    # Verify lock was released even after the unhandled exception
    assert DistributedSweeperLock._local_process_lock.locked() is False
    # Next sweep should succeed without deadlock
    sweep_post_error = await worker2._sweep_active_conditions()
    assert sweep_post_error is True


@pytest.mark.asyncio
async def test_expense_vehicle_id_auto_inheritance(db_session):
    """
    Verify that an expense linked to a trip whose vehicle_id was omitted
    is automatically attributed to the trip's vehicle in vehicle economics and fleet roll-up.
    """
    suffix = uuid.uuid4().hex[:6]
    c = Company(company_name=f"Inherit Co {suffix}", owner_name="Owner", mobile_number=f"inh_{suffix}")
    db_session.add(c)
    await db_session.flush()

    v = Vehicle(company_id=c.id, registration_number=f"TRK-INH-{suffix}")
    db_session.add(v)
    await db_session.flush()

    t = Trip(
        trip_id=f"TRP-INH-{suffix}", company_id=c.id, vehicle_id=v.id,
        status=TripStatus.COMPLETED, revenue=40000.0,
        actual_distance=300.0, actual_fuel_liters=60.0
    )
    db_session.add(t)
    await db_session.flush()

    # Expense with vehicle_id = None, but trip_id = t.id
    exp = Expense(
        company_id=c.id, vehicle_id=None, trip_id=t.id, business_id=f"EXP-NOVEH-{suffix}",
        category=ExpenseCategory.TOLL, amount=3000.0, status=ExpenseStatus.APPROVED,
        expense_date=datetime.now(timezone.utc), origin_id=str(uuid.uuid4())
    )
    db_session.add(exp)
    await db_session.flush()

    svc = VehicleEconomicsService(db_session)
    econ = await svc.get_vehicle_economics(v.id, c.id)

    assert econ.trip_linked_costs == 3000.0, "Expense with vehicle_id=None must resolve to trip's vehicle"
    assert econ.operating_profit == 37000.0

    fleet = await svc.get_fleet_roll_up(c.id)
    assert fleet.fleet_trip_linked_costs == 3000.0
    assert fleet.company_overhead_costs == 0.0, "Trip-linked expense must not become company overhead"
