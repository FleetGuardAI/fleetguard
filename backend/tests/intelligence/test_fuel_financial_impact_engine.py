import pytest
import math
import uuid
from datetime import datetime, timezone, timedelta

from models.derived_fuel_metrics import DerivedFuelMetric, EntityTypeEnum, FuelMetricType, DataQuality, MeasurementType, FuelSource
from models.entity_baseline import EntityBaseline, BaselineStatus
from models.fuel_anomaly import FuelAnomaly, AnomalyDirection, AnomalySeverity, AnomalyStatus
from models.fuel_financial_impact import FuelPriceSource
from models.operational_event import OperationalEvent, EventType, EntityType
from infrastructure.intelligence.fuel_domain.financial.engine import FuelFinancialImpactEngine

class MockFuelFinancialImpactRepository:
    def __init__(self):
        self.impacts = []

    async def upsert_impact(self, impact):
        existing = next((i for i in self.impacts if i.anomaly_reference == impact.anomaly_reference), None)
        if existing:
            self.impacts.remove(existing)
        self.impacts.append(impact)
        return impact

class MockOperationalEventRepository:
    def __init__(self):
        self.events = []

    async def list_events_by_entity(self, entity_type, entity_id, limit=500):
        return [e for e in self.events if e.entity_id == entity_id]

class MockUOW:
    def __init__(self):
        self.repositories = type('Repositories', (), {
            'fuel_financial_impact': MockFuelFinancialImpactRepository(),
            'operational_event': MockOperationalEventRepository()
        })()

def create_event(liters, odo, cost, evt_id, dt):
    return OperationalEvent(
        id=evt_id,
        event_type=EventType.FUEL_FILLED,
        entity_type=EntityType.VEHICLE,
        entity_id="TRK-1",
        occurred_at=dt,
        payload={"liters": liters, "odometer_km": odo, "cost_inr": cost, "is_full_tank": True}
    )

def create_scenario(uow, events_data):
    uow.repositories.operational_event.events = []
    evt_ids = []
    dt = datetime(2026, 8, 1, tzinfo=timezone.utc)
    for data in events_data:
        evt_id = uuid.uuid4()
        evt_ids.append(str(evt_id))
        evt = create_event(data["liters"], data["odo"], data["cost"], evt_id, dt)
        uow.repositories.operational_event.events.append(evt)
        dt += timedelta(days=1)
        
    return ",".join(evt_ids)

def get_anomaly(status=AnomalyStatus.ANOMALY, direction=AnomalyDirection.DEGRADATION):
    return FuelAnomaly(
        entity_id="TRK-1",
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        status=status,
        direction=direction,
        observation_reference="obs-123",
        baseline_reference="base-123",
        period_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 8, 10, tzinfo=timezone.utc)
    )

def get_baseline(value=2.98, status=BaselineStatus.VALID):
    return EntityBaseline(
        baseline_value=value,
        status=status
    )

def get_observation(value=2.61, source_ref=""):
    return DerivedFuelMetric(
        entity_id="TRK-1",
        entity_type=EntityTypeEnum.TRUCK,
        value=value,
        source_reference=source_ref
    )

@pytest.fixture
def engine():
    return FuelFinancialImpactEngine()

@pytest.mark.asyncio
async def test_standard_calculation(engine):
    uow = MockUOW()
    
    # Baseline = 2.98, Current = 2.61, Distance = 520, Price = 92.55/L
    source_ref = create_scenario(uow, [
        {"liters": 100, "odo": 100000, "cost": 9000}, # Excluded from price
        {"liters": 100, "odo": 100200, "cost": 9255}, 
        {"liters": 120, "odo": 100520, "cost": 11106} 
    ])
    
    # 9255 + 11106 = 20361 / 220 = 92.55
    # distance = 100520 - 100000 = 520
    
    anomaly = get_anomaly()
    baseline = get_baseline(2.98)
    observation = get_observation(2.61, source_ref)
    
    result = await engine.calculate_financial_impact(uow, anomaly, baseline, observation)
    
    assert result.status == "SUCCESS"
    assert result.distance == 520
    assert abs(result.fuel_price_per_liter - 92.55) < 0.01
    
    expected_fuel = 520 / 2.98
    implied_fuel = 520 / 2.61
    excess = implied_fuel - expected_fuel
    exposure = excess * 92.55
    
    assert abs(result.expected_fuel_liters - expected_fuel) < 0.01
    assert abs(result.implied_fuel_liters - implied_fuel) < 0.01
    assert abs(result.excess_fuel_liters - excess) < 0.01
    assert abs(result.estimated_financial_exposure - exposure) < 0.01
    assert result.fuel_price_source == FuelPriceSource.VOLUME_WEIGHTED_PURCHASE_PRICE

@pytest.mark.asyncio
async def test_exact_calculation(engine):
    uow = MockUOW()
    
    # Baseline = 5, Current = 4, Distance = 100, Price = 100
    source_ref = create_scenario(uow, [
        {"liters": 100, "odo": 100000, "cost": 9000},
        {"liters": 25, "odo": 100100, "cost": 2500}, 
    ])
    
    result = await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(5.0), get_observation(4.0, source_ref))
    
    assert result.status == "SUCCESS"
    assert result.expected_fuel_liters == 20.0
    assert result.implied_fuel_liters == 25.0
    assert result.excess_fuel_liters == 5.0
    assert result.estimated_financial_exposure == 500.0
    assert result.fuel_price_source == FuelPriceSource.ACTUAL_PURCHASE_PRICE
    
    # Check that generic fields were populated in the repository
    impacts = uow.repositories.fuel_financial_impact.impacts
    assert len(impacts) == 1
    impact_record = impacts[0]
    assert impact_record.baseline_value == 5.0
    assert impact_record.observed_value == 4.0
    assert "excess_fuel_liters" in impact_record.domain_context
    assert impact_record.domain_context["excess_fuel_liters"] == 5.0
    assert impact_record.domain_context["fuel_price_per_liter"] == 100.0
    
    # Check dual-write legacy fields
    assert impact_record.baseline_efficiency == 5.0
    assert impact_record.excess_fuel_liters == 5.0
    assert impact_record.fuel_price_per_liter == 100.0

@pytest.mark.asyncio
async def test_legacy_row_compatibility():
    """
    Test that a legacy row from the DB (missing domain_context, etc.)
    can be instantiated and still has the legacy fields accessible.
    """
    from models.fuel_financial_impact import FuelFinancialImpact
    
    legacy_row = FuelFinancialImpact(
        id=1,
        entity_id="TRK-1",
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        baseline_efficiency=3.0,
        observed_efficiency=2.5,
        distance=1000,
        expected_fuel_liters=333.33,
        implied_fuel_liters=400.0,
        excess_fuel_liters=66.67,
        fuel_price_per_liter=90.0,
        fuel_price_source=FuelPriceSource.ACTUAL_PURCHASE_PRICE,
        currency="INR",
        estimated_financial_exposure=6000.3,
        anomaly_reference="legacy_anomaly",
        baseline_reference="base_ref",
        observation_reference="obs_ref",
        period_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 8, 10, tzinfo=timezone.utc),
        calculation_method="LEGACY"
    )
    
    # Notice we did NOT supply domain_context, baseline_value, or observed_value
    assert legacy_row.domain_context is None
    assert legacy_row.baseline_value is None
    assert legacy_row.observed_value is None
    
    # Ensure legacy data is perfectly intact
    assert legacy_row.excess_fuel_liters == 66.67
    assert legacy_row.fuel_price_per_liter == 90.0
    assert legacy_row.estimated_financial_exposure == 6000.3

@pytest.mark.asyncio
async def test_zero_cost_ignored(engine):
    uow = MockUOW()
    source_ref = create_scenario(uow, [
        {"liters": 100, "odo": 100000, "cost": 9000},
        {"liters": 100, "odo": 100200, "cost": 0}, # Invalid cost
        {"liters": 100, "odo": 100520, "cost": 9300} 
    ])
    
    result = await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(5.0), get_observation(4.0, source_ref))
    assert result.status == "SUCCESS"
    assert result.fuel_price_per_liter == 93.0 # Zero cost was ignored

@pytest.mark.asyncio
async def test_improvement_returns_zero_exposure(engine):
    uow = MockUOW()
    source_ref = create_scenario(uow, [
        {"liters": 100, "odo": 100000, "cost": 9000},
        {"liters": 100, "odo": 100100, "cost": 10000}, 
    ])
    
    # anomaly says DEGRADATION but the values are actually an improvement
    result = await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(4.0), get_observation(5.0, source_ref))
    assert result.status == "SUCCESS"
    assert result.excess_fuel_liters == 0.0
    assert result.estimated_financial_exposure == 0.0

@pytest.mark.asyncio
async def test_normal_anomaly_rejected(engine):
    uow = MockUOW()
    anomaly = get_anomaly(status=AnomalyStatus.NORMAL)
    result = await engine.calculate_financial_impact(uow, anomaly, get_baseline(), get_observation())
    assert result.status == "INSUFFICIENT_DATA"

@pytest.mark.asyncio
async def test_improvement_anomaly_rejected(engine):
    uow = MockUOW()
    anomaly = get_anomaly(direction=AnomalyDirection.IMPROVEMENT)
    result = await engine.calculate_financial_impact(uow, anomaly, get_baseline(), get_observation())
    assert result.status == "INSUFFICIENT_DATA"

@pytest.mark.asyncio
async def test_insufficient_baseline(engine):
    uow = MockUOW()
    result = await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(status=BaselineStatus.INSUFFICIENT_DATA), get_observation())
    assert result.status == "INSUFFICIENT_DATA"
    assert result.reason == "BASELINE_UNAVAILABLE"

@pytest.mark.asyncio
async def test_invalid_current_efficiency(engine):
    uow = MockUOW()
    result = await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(), get_observation(-1.0))
    assert result.status == "INSUFFICIENT_DATA"
    assert result.reason == "INVALID_CURRENT_EFFICIENCY"

@pytest.mark.asyncio
async def test_invalid_distance(engine):
    uow = MockUOW()
    source_ref = create_scenario(uow, [
        {"liters": 100, "odo": 100000, "cost": 9000},
        {"liters": 100, "odo": 99000, "cost": 9000}, # Negative distance
    ])
    result = await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(), get_observation(2.61, source_ref))
    assert result.status == "INSUFFICIENT_DATA"
    assert result.reason == "INVALID_DISTANCE"

@pytest.mark.asyncio
async def test_missing_fuel_price(engine):
    uow = MockUOW()
    source_ref = create_scenario(uow, [
        {"liters": 100, "odo": 100000, "cost": 9000},
        {"liters": 100, "odo": 100520, "cost": 0}, # Only record has invalid cost
    ])
    result = await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(), get_observation(2.61, source_ref))
    assert result.status == "INSUFFICIENT_DATA"
    assert result.reason == "FUEL_PRICE_UNAVAILABLE"

@pytest.mark.asyncio
async def test_idempotency(engine):
    uow = MockUOW()
    source_ref = create_scenario(uow, [
        {"liters": 100, "odo": 100000, "cost": 9000},
        {"liters": 25, "odo": 100100, "cost": 2500}, 
    ])
    
    await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(5.0), get_observation(4.0, source_ref))
    await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(5.0), get_observation(4.0, source_ref))
    
    assert len(uow.repositories.fuel_financial_impact.impacts) == 1
    assert uow.repositories.fuel_financial_impact.impacts[0].anomaly_reference == "obs-123"

@pytest.mark.asyncio
async def test_recalculation_after_missing_price(engine):
    uow = MockUOW()
    source_ref = create_scenario(uow, [
        {"liters": 100, "odo": 100000, "cost": 9000},
        {"liters": 100, "odo": 100520, "cost": 0}, 
    ])
    
    # First attempt: fails
    res1 = await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(), get_observation(2.61, source_ref))
    assert res1.status == "INSUFFICIENT_DATA"
    assert len(uow.repositories.fuel_financial_impact.impacts) == 0
    
    # Price is updated
    uow.repositories.operational_event.events[1].payload["cost_inr"] = 9200
    
    # Second attempt: succeeds
    res2 = await engine.calculate_financial_impact(uow, get_anomaly(), get_baseline(), get_observation(2.61, source_ref))
    assert res2.status == "SUCCESS"
    assert len(uow.repositories.fuel_financial_impact.impacts) == 1
