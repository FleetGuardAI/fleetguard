import pytest
from services.pre_trip_intelligence import PreTripIntelligenceService
from schemas.pre_trip_intelligence import (
    PreTripEvaluateRequest,
    RecommendationDecision,
    RiskLevel,
    ConfidenceLevel
)


@pytest.mark.asyncio
async def test_fuel_and_cost_calculation(db_session):
    service = PreTripIntelligenceService(db_session)
    req = PreTripEvaluateRequest(
        planned_distance=1000.0,
        revenue=50000.0,
        planned_cost=10000.0
    )
    result = await service.evaluate_trip(req, company_id=1)

    # 1000 km / 4.0 km/L = 250 liters
    assert result.expected_fuel_liters == 250.0
    # 250 L * 100 Rs/L = 25000 Rs
    assert result.expected_fuel_cost == 25000.0
    assert result.expected_total_cost > 0
    assert result.expected_profit is not None


@pytest.mark.asyncio
async def test_take_decision(db_session):
    from models.vehicle_domain import Vehicle, VehicleStatus
    # High revenue relative to cost and suitable vehicle assigned -> Healthy margin >= 15% -> TAKE
    v = Vehicle(company_id=1, registration_number="MH-01-TAKE", status=VehicleStatus.ACTIVE)
    db_session.add(v)
    await db_session.flush()

    service = PreTripIntelligenceService(db_session)
    req = PreTripEvaluateRequest(
        vehicle_id=v.id,
        origin_location="Mumbai",
        destination_location="Pune",
        planned_distance=100.0,
        revenue=100000.0,
        planned_cost=5000.0
    )
    result = await service.evaluate_trip(req, company_id=1)
    assert result.recommendation == RecommendationDecision.TAKE
    assert result.risk_level == RiskLevel.LOW


@pytest.mark.asyncio
async def test_avoid_decision(db_session):
    # Revenue below total cost -> Loss / negative margin -> AVOID
    service = PreTripIntelligenceService(db_session)
    req = PreTripEvaluateRequest(
        planned_distance=500.0,
        revenue=1000.0,
        planned_cost=50000.0
    )
    result = await service.evaluate_trip(req, company_id=1)
    assert result.recommendation == RecommendationDecision.AVOID
    assert result.risk_level == RiskLevel.HIGH


@pytest.mark.asyncio
async def test_minimum_freight(db_session):
    service = PreTripIntelligenceService(db_session)
    req = PreTripEvaluateRequest(
        planned_distance=500.0,
        revenue=30000.0
    )
    result = await service.evaluate_trip(req, company_id=1)
    assert result.minimum_recommended_freight is not None
    assert result.minimum_recommended_freight > 0


@pytest.mark.asyncio
async def test_missing_revenue(db_session):
    service = PreTripIntelligenceService(db_session)
    req = PreTripEvaluateRequest(
        planned_distance=1000.0,
        revenue=None
    )
    result = await service.evaluate_trip(req, company_id=1)
    # Without revenue, profit and margin cannot be calculated
    assert result.expected_profit is None
    assert result.expected_margin_pct is None
    assert result.recommendation == RecommendationDecision.REVIEW
