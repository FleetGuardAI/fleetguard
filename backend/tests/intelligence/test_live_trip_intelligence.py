import pytest
from datetime import datetime, timezone, timedelta
from services.live_trip_intelligence import LiveTripIntelligenceService
from schemas.live_trip_intelligence import TripHealthStatus
from models.trip_domain import Trip
from models.expense_domain import Expense, ExpenseStatus, ExpenseCategory
import uuid


@pytest.mark.asyncio
async def test_on_track_health(db_session):
    now = datetime.now(timezone.utc)
    trip = Trip(
        id=9901,
        trip_id=f"TRIP-{uuid.uuid4().hex[:6]}",
        actual_start_time=now - timedelta(hours=2),
        planned_end_time=now + timedelta(hours=8),
        expected_cost=10000.0,
        expected_profit=15000.0,
        expected_revenue=25000.0,
        intelligence_snapshot={
            "expected_total_cost": 10000.0,
            "expected_profit": 15000.0,
            "expected_revenue": 25000.0,
            "expected_duration_hours": 10.0
        }
    )
    service = LiveTripIntelligenceService(db_session)
    result = await service.compute_live_health(trip)
    assert result.health_status == TripHealthStatus.ON_TRACK
    assert len(result.deviations) == 0


@pytest.mark.asyncio
async def test_profit_erosion(db_session):
    now = datetime.now(timezone.utc)
    trip = Trip(
        id=9902,
        trip_id=f"TRIP-{uuid.uuid4().hex[:6]}",
        actual_start_time=now - timedelta(hours=5),
        planned_end_time=now + timedelta(hours=5),
        expected_cost=10000.0,
        expected_profit=15000.0,
        expected_revenue=25000.0,
        intelligence_snapshot={
            "expected_total_cost": 10000.0,
            "expected_profit": 15000.0,
            "expected_revenue": 25000.0,
            "expected_duration_hours": 10.0
        }
    )
    # Add an approved expense exceeding planned cost
    exp = Expense(
        trip_id=trip.id,
        company_id=1,
        vehicle_id=1,
        business_id=f"EXP-{uuid.uuid4().hex[:6]}",
        origin_id=str(uuid.uuid4()),
        category=ExpenseCategory.FUEL,
        amount=14000.0,
        status=ExpenseStatus.APPROVED,
        expense_date=now
    )
    db_session.add(exp)
    await db_session.flush()

    service = LiveTripIntelligenceService(db_session)
    result = await service.compute_live_health(trip)

    assert result.projected_total_cost >= 14000.0
    assert result.profit_erosion > 0
    assert result.health_status in [TripHealthStatus.AT_RISK, TripHealthStatus.CRITICAL]


@pytest.mark.asyncio
async def test_time_deviation(db_session):
    now = datetime.now(timezone.utc)
    # Expected duration was 10 hours. It has been 14 hours.
    trip = Trip(
        id=9903,
        trip_id=f"TRIP-{uuid.uuid4().hex[:6]}",
        actual_start_time=now - timedelta(hours=14),
        expected_cost=10000.0,
        expected_profit=5000.0,
        expected_revenue=15000.0,
        intelligence_snapshot={
            "expected_total_cost": 10000.0,
            "expected_profit": 5000.0,
            "expected_revenue": 15000.0,
            "expected_duration_hours": 10.0
        }
    )
    service = LiveTripIntelligenceService(db_session)
    result = await service.compute_live_health(trip)

    # 14 hours vs 10 hours = 40% variance -> CRITICAL duration deviation
    assert result.health_status in [TripHealthStatus.AT_RISK, TripHealthStatus.CRITICAL]
    assert any(d.metric == "Duration" for d in result.deviations)
