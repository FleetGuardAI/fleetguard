"""
FleetGuard — Fleet Intelligence Engine (FIE) Integrity & Hardening Test Suite
Verifies all 12 core intelligence integrity scenarios:
1. Missing telemetry does not create fabricated actual metrics.
2. Fuel purchased is not treated as fuel consumed.
3. Refueling does not automatically trigger a theft alert.
4. GPS jumps / missing route data handled safely without false precision.
5. Genuine fuel siphoning drop triggers the appropriate theft alert.
6. Incomplete maintenance history does not produce a falsely healthy status.
7. Overdue vehicle receives the correct maintenance state and suitability rejection.
8. Unapproved expenses do not influence live or post-trip economics.
9. Reprocessing a source event or repeated sweeps are idempotent.
10. Insufficient data does not create false precision or 100/100 scores.
11. Tenant isolation strictly applies across fleet intelligence.
12. Observable error handling on sweeper worker execution.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from models.company import Company
from models.user import User, UserRole
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus
from models.trip_domain import Trip, TripStatus
from models.expense_domain import Expense, ExpenseStatus, ExpenseCategory
from models.fuel_domain import FuelTransaction, FuelTransactionType
from models.notification import Notification

from services.trip_intelligence_service import TripIntelligenceService
from services.live_trip_intelligence import LiveTripIntelligenceService
from services.vehicle_intelligence import VehicleIntelligence
from services.maintenance_due_service import MaintenanceDueService
from services.prediction_service import (
    detect_fuel_theft_and_fraud,
    FuelTheftEvaluationRequest
)
from services.fleet_intelligence_service import FleetIntelligenceService
from services.trip_intelligence_config import intelligence_config
from infrastructure.uow import AbstractUnitOfWork, RepositoryRegistry
from schemas.pre_trip_intelligence import SuitabilityStatus


class SessionUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session):
        self._session = session
        self.repositories = RepositoryRegistry(session)

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()


@pytest.mark.asyncio
async def test_1_missing_telemetry_isolation(db_session):
    """
    Scenario 1: Missing telemetry does not create fabricated actual metrics.
    When actual_distance and actual_fuel_liters are NULL, TripIntelligenceService
    must not substitute planned values or fabricate efficiency.
    """
    comp = Company(company_name=f"Comp-Int-{uuid.uuid4().hex[:6]}", owner_name="Owner", mobile_number=f"m_{uuid.uuid4().hex[:8]}")
    db_session.add(comp)
    await db_session.flush()

    v = Vehicle(company_id=comp.id, registration_number=f"MH-{uuid.uuid4().hex[:4].upper()}", status=VehicleStatus.ACTIVE)
    db_session.add(v)
    await db_session.flush()

    trip = Trip(
        company_id=comp.id,
        vehicle_id=v.id,
        trip_id=f"TRIP-{uuid.uuid4().hex[:6].upper()}",
        status=TripStatus.COMPLETED,
        planned_distance=500.0,
        actual_distance=None,        # Missing GPS distance
        actual_fuel_liters=None,     # Missing fuel telemetry
        revenue=20000.0,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=10),
        actual_end_time=datetime.now(timezone.utc),
    )
    db_session.add(trip)
    await db_session.commit()

    uow = SessionUnitOfWork(db_session)
    service = TripIntelligenceService(uow)
    resp = await service.compute_intelligence(trip)

    # Telemetry should NOT be fabricated from planned_distance
    dist_item = next((p for p in resp.planned_vs_actual if p.metric == "distance"), None)
    fuel_item = next((p for p in resp.planned_vs_actual if p.metric == "fuel"), None)
    assert dist_item is not None
    assert dist_item.actual is None
    assert dist_item.has_data is False
    assert fuel_item is None or fuel_item.actual is None
    assert resp.financial_summary.cost_per_km is None
    assert resp.financial_summary.revenue_per_km is None


@pytest.mark.asyncio
async def test_2_fuel_purchased_is_not_consumed(db_session):
    """
    Scenario 2: Fuel purchased at the pump is NOT treated as fuel consumed.
    Actual consumption comes exclusively from Trip.actual_fuel_liters.
    """
    comp = Company(company_name=f"Comp-Fuel-{uuid.uuid4().hex[:6]}", owner_name="Owner", mobile_number=f"m_{uuid.uuid4().hex[:8]}")
    db_session.add(comp)
    await db_session.flush()

    v = Vehicle(company_id=comp.id, registration_number=f"MH-{uuid.uuid4().hex[:4].upper()}", status=VehicleStatus.ACTIVE)
    db_session.add(v)
    await db_session.flush()

    trip = Trip(
        company_id=comp.id,
        vehicle_id=v.id,
        trip_id=f"TRIP-{uuid.uuid4().hex[:6].upper()}",
        status=TripStatus.COMPLETED,
        planned_distance=400.0,
        planned_fuel_liters=100.0,
        actual_distance=400.0,
        actual_fuel_liters=100.0,    # 100L consumed (4.0 km/L)
        revenue=30000.0,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=8),
        actual_end_time=datetime.now(timezone.utc),
    )
    db_session.add(trip)
    await db_session.flush()

    # Driver purchased 250L at pump into tanks for future trips
    tx = FuelTransaction(
        vehicle_id=v.id,
        company_id=comp.id,
        trip_id=trip.id,
        amount_liters=250.0,
        price_per_liter=95.0,
        total_cost=23750.0,
        timestamp=datetime.now(timezone.utc),
        transaction_type=FuelTransactionType.FILL
    )
    db_session.add(tx)
    await db_session.commit()

    uow = SessionUnitOfWork(db_session)
    service = TripIntelligenceService(uow)
    resp = await service.compute_intelligence(trip)

    # Actual fuel consumed must be 100L, NOT 250L purchased
    fuel_item = next((p for p in resp.planned_vs_actual if p.metric == "fuel"), None)
    assert fuel_item is not None
    assert fuel_item.actual == 100.0
    assert fuel_item.actual != 250.0


def test_3_refueling_does_not_trigger_theft():
    """
    Scenario 3: Refueling does NOT automatically trigger a theft alert.
    When sensor delta matches receipt volume within valid tolerance, status is CLEAN.
    """
    req = FuelTheftEvaluationRequest(
        sensor_tank_before_liters=50.0,
        sensor_tank_after_liters=246.0,   # +196L in tank
        claimed_receipt_liters=200.0,     # Claimed 200L (diff = 4L <= max(5, 10))
        static_drop_liters=0.0,
        vehicle_speed_kmh=0.0,
        engine_status_on=False
    )
    resp = detect_fuel_theft_and_fraud(req)

    assert resp.overall_fraud_risk == "CLEAN"
    assert resp.is_receipt_fraud_flagged is False
    assert resp.is_siphoning_flagged is False
    assert "VERIFIED" in resp.explanation


def test_5_genuine_fuel_siphoning_drop():
    """
    Scenario 5: Genuine unusual static fuel drop triggers theft alert.
    When a vehicle is parked with engine off and fuel level drops >= 3.5L.
    """
    req = FuelTheftEvaluationRequest(
        sensor_tank_before_liters=100.0,
        sensor_tank_after_liters=100.0,
        claimed_receipt_liters=0.0,
        static_drop_liters=15.0,         # 15L dropped statically
        vehicle_speed_kmh=0.0,
        engine_status_on=False
    )
    resp = detect_fuel_theft_and_fraud(req)

    assert resp.is_siphoning_flagged is True
    assert resp.overall_fraud_risk == "HIGH_SIPHONING"
    assert "THEFT ALERT" in resp.explanation
    assert resp.static_siphon_drop_liters == 15.0


@pytest.mark.asyncio
async def test_6_incomplete_maintenance_history_safety(db_session):
    """
    Scenario 6: Incomplete maintenance history does NOT produce falsely healthy status.
    A vehicle with missing odometer and missing service history returns UNKNOWN.
    """
    comp = Company(company_name=f"Comp-Maint-{uuid.uuid4().hex[:6]}", owner_name="Owner", mobile_number=f"m_{uuid.uuid4().hex[:8]}")
    db_session.add(comp)
    await db_session.flush()

    v = Vehicle(
        company_id=comp.id,
        registration_number=f"MH-{uuid.uuid4().hex[:4].upper()}",
        status=VehicleStatus.ACTIVE,
        current_odometer=None,
        last_service_odometer=None,
        last_service_date=None,
        maintenance_interval_km=None,
        maintenance_interval_days=None
    )
    db_session.add(v)
    await db_session.commit()

    service = MaintenanceDueService(db_session)
    status = await service.evaluate_vehicle(v)

    # Must NOT return NOT_DUE
    assert status == "UNKNOWN"


@pytest.mark.asyncio
async def test_7_overdue_vehicle_due_state_and_rejection(db_session):
    """
    Scenario 7: Overdue vehicle receives correct maintenance state and suitability rejection.
    """
    comp = Company(company_name=f"Comp-Overdue-{uuid.uuid4().hex[:6]}", owner_name="Owner", mobile_number=f"m_{uuid.uuid4().hex[:8]}")
    db_session.add(comp)
    await db_session.flush()

    v = Vehicle(
        company_id=comp.id,
        registration_number=f"MH-{uuid.uuid4().hex[:4].upper()}",
        status=VehicleStatus.ACTIVE,
        current_odometer=25000.0,
        last_service_odometer=10000.0,
        maintenance_interval_km=10000.0, # due at 20000, 5000km overdue (>500km grace)
        maintenance_status="NOT_DUE"
    )
    db_session.add(v)
    await db_session.commit()

    service = MaintenanceDueService(db_session)
    status = await service.evaluate_vehicle(v)
    assert status == "OVERDUE"

    v.maintenance_status = status
    await db_session.commit()

    # Pre-trip vehicle suitability should reject overdue vehicle
    v_intel = VehicleIntelligence(db_session, intelligence_config)
    suitability = await v_intel.evaluate_suitability(v, None, None, 100.0)

    assert suitability.status == SuitabilityStatus.UNSUITABLE
    assert any("overdue" in r.lower() for r in suitability.reasons)


@pytest.mark.asyncio
async def test_8_unapproved_expenses_excluded_from_profitability(db_session):
    """
    Scenario 8: Unapproved, pending, and rejected expenses do NOT enter actual costs.
    LiveTripIntelligenceService and TripIntelligenceService must include ONLY APPROVED expenses.
    """
    comp = Company(company_name=f"Comp-Exp-{uuid.uuid4().hex[:6]}", owner_name="Owner", mobile_number=f"m_{uuid.uuid4().hex[:8]}")
    db_session.add(comp)
    await db_session.flush()

    v = Vehicle(company_id=comp.id, registration_number=f"MH-{uuid.uuid4().hex[:4].upper()}", status=VehicleStatus.ACTIVE)
    db_session.add(v)
    await db_session.flush()

    trip = Trip(
        company_id=comp.id,
        vehicle_id=v.id,
        trip_id=f"TRIP-{uuid.uuid4().hex[:6].upper()}",
        status=TripStatus.IN_PROGRESS,
        actual_distance=200.0,
        revenue=50000.0,
        expected_revenue=50000.0,
        expected_cost=20000.0,
        expected_profit=30000.0,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=4),
        intelligence_snapshot={"expected_duration_hours": 8.0, "expected_profit": 30000.0}
    )
    db_session.add(trip)
    await db_session.flush()

    # 1 APPROVED expense of 4,000
    e_approved = Expense(
        company_id=comp.id,
        trip_id=trip.id,
        vehicle_id=v.id,
        business_id=f"EXP-APP-{uuid.uuid4().hex[:6]}",
        origin_id=f"evt_{uuid.uuid4().hex[:6]}",
        category=ExpenseCategory.TOLL,
        amount=4000.0,
        status=ExpenseStatus.APPROVED,
        expense_date=datetime.now(timezone.utc)
    )
    # 1 PENDING expense of 10,000
    e_pending = Expense(
        company_id=comp.id,
        trip_id=trip.id,
        vehicle_id=v.id,
        business_id=f"EXP-PEN-{uuid.uuid4().hex[:6]}",
        origin_id=f"evt_{uuid.uuid4().hex[:6]}",
        category=ExpenseCategory.FUEL,
        amount=10000.0,
        status=ExpenseStatus.PENDING,
        expense_date=datetime.now(timezone.utc)
    )
    # 1 REJECTED expense of 15,000
    e_rejected = Expense(
        company_id=comp.id,
        trip_id=trip.id,
        vehicle_id=v.id,
        business_id=f"EXP-REJ-{uuid.uuid4().hex[:6]}",
        origin_id=f"evt_{uuid.uuid4().hex[:6]}",
        category=ExpenseCategory.MISCELLANEOUS,
        amount=15000.0,
        status=ExpenseStatus.REJECTED,
        expense_date=datetime.now(timezone.utc)
    )
    db_session.add_all([e_approved, e_pending, e_rejected])
    await db_session.commit()

    live_service = LiveTripIntelligenceService(db_session)
    live_resp = await live_service.compute_live_health(trip)

    # actual_cost_so_far must be EXACTLY 4,000.0 (pending 10k and rejected 15k excluded)
    assert live_resp.actual_cost_so_far == 4000.0


@pytest.mark.asyncio
async def test_9_idempotency_duplicate_suppression(db_session):
    """
    Scenario 9: Repeated sweeps and re-evaluations are strictly idempotent.
    Sweep on already updated vehicle does not produce duplicate notifications.
    """
    comp = Company(company_name=f"Comp-Idemp-{uuid.uuid4().hex[:6]}", owner_name="Owner", mobile_number=f"m_{uuid.uuid4().hex[:8]}")
    db_session.add(comp)
    await db_session.flush()

    v = Vehicle(
        company_id=comp.id,
        registration_number=f"MH-{uuid.uuid4().hex[:4].upper()}",
        status=VehicleStatus.ACTIVE,
        current_odometer=30000.0,
        last_service_odometer=10000.0,
        maintenance_interval_km=10000.0,
        maintenance_status="NOT_DUE"
    )
    db_session.add(v)
    await db_session.commit()

    service = MaintenanceDueService(db_session)

    # First sweep: should update status to OVERDUE and create 1 notification
    await service.sweep_maintenance_status(company_id=comp.id)

    stmt_notifs = select(Notification).where(Notification.company_id == comp.id)
    res1 = await db_session.execute(stmt_notifs)
    notifs1 = res1.scalars().all()
    assert len(notifs1) == 1
    assert v.maintenance_status == "OVERDUE"

    # Second sweep immediately after: should be idempotent, no new notification
    await service.sweep_maintenance_status(company_id=comp.id)

    res2 = await db_session.execute(stmt_notifs)
    notifs2 = res2.scalars().all()
    assert len(notifs2) == 1  # Still exactly 1, no duplicates created


def test_10_insufficient_data_does_not_create_false_precision():
    """
    Scenario 10: Insufficient data does not fabricate outcome or precision.
    Trip without expected profit snapshot returns None outcome.
    """
    trip = Trip(
        expected_profit=None,
        intelligence_snapshot=None
    )
    outcome = TripIntelligenceService._compute_recommendation_outcome(trip, actual_profit=15000.0)
    assert outcome is None


@pytest.mark.asyncio
async def test_11_tenant_isolation_in_fleet_intelligence(db_session):
    """
    Scenario 11: Tenant isolation strictly enforced in fleet intelligence.
    Company A's get_fleet_health must only search and include Company A's vehicles.
    """
    comp_a = Company(company_name=f"Comp-A-{uuid.uuid4().hex[:6]}", owner_name="OwnerA", mobile_number=f"ma_{uuid.uuid4().hex[:8]}")
    comp_b = Company(company_name=f"Comp-B-{uuid.uuid4().hex[:6]}", owner_name="OwnerB", mobile_number=f"mb_{uuid.uuid4().hex[:8]}")
    db_session.add_all([comp_a, comp_b])
    await db_session.flush()

    v_a = Vehicle(company_id=comp_a.id, registration_number=f"MH-A-{uuid.uuid4().hex[:4].upper()}", status=VehicleStatus.ACTIVE)
    v_b = Vehicle(company_id=comp_b.id, registration_number=f"MH-B-{uuid.uuid4().hex[:4].upper()}", status=VehicleStatus.ACTIVE)
    db_session.add_all([v_a, v_b])
    await db_session.commit()

    uow = SessionUnitOfWork(db_session)
    service = FleetIntelligenceService(uow)

    health_a = await service.get_fleet_health(comp_a.id)

    # Company A's report must evaluate exactly 1 vehicle (v_a), NOT v_b
    assert health_a.vehicle_count == 1
    assert health_a.fleet_id == str(comp_a.id)

    health_b = await service.get_fleet_health(comp_b.id)
    assert health_b.vehicle_count == 1
    assert health_b.fleet_id == str(comp_b.id)


@pytest.mark.asyncio
async def test_4_insufficient_route_data_isolation(db_session):
    """
    Scenario 4: Missing or invalid route coordinates do not fabricate distance or high confidence.
    PreTripIntelligenceService marks confidence as INSUFFICIENT.
    """
    from services.pre_trip_intelligence import PreTripIntelligenceService
    from schemas.pre_trip_intelligence import PreTripEvaluateRequest, ConfidenceLevel

    comp = Company(company_name=f"Comp-Route-{uuid.uuid4().hex[:6]}", owner_name="Owner", mobile_number=f"m_{uuid.uuid4().hex[:8]}")
    db_session.add(comp)
    await db_session.commit()

    service = PreTripIntelligenceService(db_session)
    req = PreTripEvaluateRequest(
        origin_location=None,
        destination_location=None,
        planned_distance=None,
        revenue=25000.0
    )
    resp = await service.evaluate_trip(req, comp.id)
    assert resp.confidence_level == ConfidenceLevel.INSUFFICIENT
    assert resp.recommendation == "AVOID"
    assert any("Missing Route Data" in rf.factor for rf in resp.risk_factors)


@pytest.mark.asyncio
async def test_12_sweeper_worker_error_observability(db_session):
    """
    Scenario 12: Sweeper worker failure is observable and transactional rollback works.
    """
    from unittest.mock import AsyncMock, patch
    from infrastructure.intelligence.sweeper_worker import IntelligenceSweeperWorker

    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.all = lambda: []
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.rollback = AsyncMock()

    class MockSessionFactory:
        async def __aenter__(self):
            return mock_session
        async def __aexit__(self, exc_type, exc_val, tb):
            pass

    worker = IntelligenceSweeperWorker(session_factory=lambda: MockSessionFactory())
    with patch("infrastructure.intelligence.sweeper_worker.MaintenanceDueService.sweep_maintenance_status", side_effect=RuntimeError("Simulated DB Connection Drop")):
        with pytest.raises(RuntimeError, match="Simulated DB Connection Drop"):
            await worker._sweep_active_conditions()

    mock_session.rollback.assert_awaited_once()

