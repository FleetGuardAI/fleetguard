import pytest
from datetime import datetime, timezone, timedelta
from services.live_trip_intelligence import LiveTripIntelligenceService
from services.trip_intelligence_config import TripIntelligenceConfig
from models.trip_domain import Trip

@pytest.fixture
def mock_config():
    return TripIntelligenceConfig(
        time_variance_warning_pct=0.15,
        time_variance_critical_pct=0.30,
        cost_variance_warning_pct=0.10,
        cost_variance_critical_pct=0.20
    )

@pytest.fixture
def service(mock_config):
    return LiveTripIntelligenceService(mock_config)

def test_on_track_health(service):
    trip = Trip(
        start_date=datetime.now(timezone.utc) - timedelta(hours=2),
        expected_delivery=datetime.now(timezone.utc) + timedelta(hours=8),
        distance_km=500,
        planned_cost=10000,
        fuel_cost=0,
        driver_cost=0,
        toll_cost=0,
        other_expenses=0,
        intelligence_snapshot={
            "expected_total_cost": 10000,
            "expected_profit": 15000,
            "expected_revenue": 25000,
            "expected_duration_hours": 10
        }
    )
    result = service.evaluate_live_trip(trip)
    assert result.health_status == "ON_TRACK"
    assert len(result.deviations) == 0

def test_profit_erosion(service):
    # Actual costs far exceed planned, eroding profit
    trip = Trip(
        start_date=datetime.now(timezone.utc) - timedelta(hours=5),
        expected_delivery=datetime.now(timezone.utc) + timedelta(hours=5),
        distance_km=500,
        planned_cost=10000,
        fuel_cost=12000,  # Unexpectedly high
        driver_cost=0,
        toll_cost=0,
        other_expenses=0,
        intelligence_snapshot={
            "expected_total_cost": 10000,
            "expected_profit": 15000,
            "expected_revenue": 25000,
            "expected_duration_hours": 10
        }
    )
    result = service.evaluate_live_trip(trip)
    # Expected profit was 15k. Actual cost is already 12k. Revenue 25k -> Projected Profit <= 13k.
    assert result.projected_total_cost >= 12000
    assert result.projected_profit <= 13000
    assert result.profit_erosion > 0
    assert result.health_status in ["AT_RISK", "CRITICAL"]

def test_time_deviation(service):
    # Expected duration was 10 hours. It's been 12 hours.
    trip = Trip(
        start_date=datetime.now(timezone.utc) - timedelta(hours=12),
        expected_delivery=datetime.now(timezone.utc) - timedelta(hours=2),
        distance_km=500,
        intelligence_snapshot={
            "expected_duration_hours": 10
        }
    )
    result = service.evaluate_live_trip(trip)
    # Variance = (12 - 10) / 10 = 0.20 (20%) -> Between 15% and 30%, so AT_RISK
    assert result.health_status == "AT_RISK"
    assert any(d.metric == "Duration" for d in result.deviations)
