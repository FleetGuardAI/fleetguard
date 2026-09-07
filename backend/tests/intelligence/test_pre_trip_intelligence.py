import pytest
from datetime import datetime, timezone
from services.pre_trip_intelligence import PreTripIntelligenceService
from services.trip_intelligence_config import TripIntelligenceConfig
from schemas.pre_trip_intelligence import PreTripEvaluateRequest

@pytest.fixture
def mock_config():
    return TripIntelligenceConfig(
        target_margin_pct=0.15,
        minimum_acceptable_margin_pct=0.05,
        default_fuel_price=95.0,
        default_fuel_efficiency_kmpl=4.0
    )

@pytest.fixture
def service(mock_config):
    return PreTripIntelligenceService(mock_config)

def test_fuel_and_cost_calculation(service):
    req = PreTripEvaluateRequest(
        planned_distance=1000,
        revenue=50000,
        planned_cost=10000,
        planned_fuel_liters=None
    )
    result = service.evaluate_trip(req)
    
    # Expected fuel = 1000 / 4.0 = 250 liters
    assert result.expected_fuel_liters == 250
    # Expected fuel cost = 250 * 95.0 = 23750
    assert result.expected_fuel_cost == 23750
    # Expected total cost = 10000 + 23750 = 33750
    assert result.expected_total_cost == 33750
    # Expected profit = 50000 - 33750 = 16250
    assert result.expected_profit == 16250
    # Margin = 16250 / 50000 = 0.325
    assert result.expected_margin_pct == pytest.approx(0.325)

def test_take_decision(service):
    # 50,000 revenue, 25,000 cost -> 50% margin (> 15% target)
    req = PreTripEvaluateRequest(planned_distance=100, revenue=50000, planned_cost=25000, planned_fuel_liters=0)
    result = service.evaluate_trip(req)
    assert result.recommendation == "TAKE"
    assert result.risk_level == "LOW"

def test_review_decision(service):
    # 50,000 revenue, 45,000 cost -> 10% margin (between 5% and 15%)
    req = PreTripEvaluateRequest(planned_distance=100, revenue=50000, planned_cost=45000, planned_fuel_liters=0)
    result = service.evaluate_trip(req)
    assert result.recommendation == "REVIEW"
    assert result.risk_level == "MEDIUM"

def test_avoid_decision(service):
    # 50,000 revenue, 49,000 cost -> 2% margin (< 5% minimum)
    req = PreTripEvaluateRequest(planned_distance=100, revenue=50000, planned_cost=49000, planned_fuel_liters=0)
    result = service.evaluate_trip(req)
    assert result.recommendation == "AVOID"
    assert result.risk_level == "HIGH"

def test_minimum_freight(service):
    # 33,750 expected total cost. Min freight for 15% margin = 33,750 / (1 - 0.15) = 39705.88
    req = PreTripEvaluateRequest(
        planned_distance=1000,
        revenue=30000,
        planned_cost=10000
    )
    result = service.evaluate_trip(req)
    assert result.minimum_recommended_freight == pytest.approx(39705.88, abs=0.01)

def test_missing_revenue(service):
    req = PreTripEvaluateRequest(
        planned_distance=1000,
        revenue=None,
        planned_cost=10000
    )
    result = service.evaluate_trip(req)
    # Without revenue, we can't calculate profit/margin or make a decision based on economics
    assert result.expected_profit is None
    assert result.expected_margin_pct is None
    # Assuming without revenue, it defaults to REVIEW and INSUFFICIENT confidence
    assert result.recommendation == "REVIEW"
    assert result.confidence_level == "INSUFFICIENT"
    assert result.risk_level == "MEDIUM"
