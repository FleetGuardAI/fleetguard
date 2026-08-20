import pytest
import math
from datetime import datetime, timezone

from models.derived_fuel_metrics import DerivedFuelMetric, EntityTypeEnum, FuelMetricType, DataQuality, MeasurementType, FuelSource
from models.entity_baseline import EntityBaseline, BaselineStatus
from models.fuel_anomaly import FuelAnomaly, AnomalyDirection, AnomalySeverity, AnomalyStatus
from infrastructure.intelligence.fuel_domain.anomaly.engine import FuelAnomalyEngine
from config import settings

class MockFuelAnomalyRepository:
    def __init__(self):
        self.anomalies = []

    async def upsert_anomaly(self, anomaly):
        # Implement idempotency behavior roughly
        existing = next((a for a in self.anomalies if a.observation_reference == anomaly.observation_reference), None)
        if existing:
            self.anomalies.remove(existing)
        self.anomalies.append(anomaly)
        return anomaly

class MockUOW:
    def __init__(self):
        self.repositories = type('Repositories', (), {
            'fuel_anomaly': MockFuelAnomalyRepository()
        })()

def create_observation(value, metric_type=FuelMetricType.FUEL_EFFICIENCY, quality=DataQuality.HIGH, measurement_type=MeasurementType.DERIVED, obs_id=100, entity_id="TRK-1"):
    metric = DerivedFuelMetric(
        entity_id=entity_id,
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=metric_type,
        value=value,
        unit="KM_PER_LITRE",
        source=FuelSource.ODOMETER_FUEL,
        quality=quality,
        measurement_type=measurement_type,
        period_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 8, 2, tzinfo=timezone.utc),
        sample_size=1
    )
    metric.id = obs_id
    return metric

def create_baseline(value, status=BaselineStatus.VALID, sample_size=10, baseline_id=1, entity_id="TRK-1", metric_type=FuelMetricType.FUEL_EFFICIENCY):
    baseline = EntityBaseline(
        entity_id=entity_id,
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=metric_type,
        baseline_value=value,
        unit="KM_PER_LITRE",
        sample_size=sample_size,
        calculation_method="MEDIAN",
        data_quality=DataQuality.HIGH,
        status=status,
        period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 7, 31, tzinfo=timezone.utc)
    )
    baseline.id = baseline_id
    return baseline

@pytest.fixture
def engine():
    return FuelAnomalyEngine()

@pytest.mark.asyncio
async def test_normal_baseline_normal_observation(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00)
    observation = create_observation(2.95)
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    assert result.status == AnomalyStatus.NORMAL
    assert result.severity == AnomalySeverity.NORMAL
    assert result.direction == AnomalyDirection.DEGRADATION
    assert result.deviation_percent == -1.6667
    assert len(uow.repositories.fuel_anomaly.anomalies) == 1

@pytest.mark.asyncio
async def test_warning_anomaly(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00)
    observation = create_observation(2.65) # -11.66%
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    assert result.status == AnomalyStatus.ANOMALY
    assert result.severity == AnomalySeverity.WARNING
    assert result.direction == AnomalyDirection.DEGRADATION

@pytest.mark.asyncio
async def test_critical_anomaly(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00)
    observation = create_observation(2.35) # -21.66%
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    assert result.status == AnomalyStatus.ANOMALY
    assert result.severity == AnomalySeverity.CRITICAL
    assert result.direction == AnomalyDirection.DEGRADATION

@pytest.mark.asyncio
async def test_improvement(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00)
    observation = create_observation(3.30) # +10%
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    assert result.status == AnomalyStatus.NORMAL
    assert result.severity == AnomalySeverity.NORMAL
    assert result.direction == AnomalyDirection.IMPROVEMENT

@pytest.mark.asyncio
async def test_exactly_threshold(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00)
    observation = create_observation(2.70) # Exactly -10%
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    # Deviation is -10.0. 
    # warning threshold = 10.0
    # deviation <= -warning_threshold -> WARNING
    # -10.0 <= -10.0 is True.
    assert result.status == AnomalyStatus.ANOMALY
    assert result.severity == AnomalySeverity.WARNING

@pytest.mark.asyncio
async def test_missing_baseline(engine):
    uow = MockUOW()
    observation = create_observation(2.95)
    
    result = await engine.detect_anomaly(uow, observation, None)
    
    assert result.status == AnomalyStatus.INSUFFICIENT_DATA
    assert result.reason == "BASELINE_UNAVAILABLE"
    assert len(uow.repositories.fuel_anomaly.anomalies) == 0

@pytest.mark.asyncio
async def test_invalid_baseline(engine):
    uow = MockUOW()
    baseline = create_baseline(0) # Zero baseline
    observation = create_observation(2.95)
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    assert result.status == AnomalyStatus.INSUFFICIENT_DATA
    
    baseline2 = create_baseline(3.00, status=BaselineStatus.INSUFFICIENT_DATA)
    result = await engine.detect_anomaly(uow, observation, baseline2)
    assert result.status == AnomalyStatus.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_invalid_observation(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00)
    
    for val in [0, -1, math.nan, math.inf, None]:
        obs = create_observation(val)
        result = await engine.detect_anomaly(uow, obs, baseline)
        assert result.status == AnomalyStatus.INSUFFICIENT_DATA
        assert result.reason == "INVALID_CURRENT_OBSERVATION"

@pytest.mark.asyncio
async def test_estimated_observation(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00)
    observation = create_observation(2.65, measurement_type=MeasurementType.ESTIMATED)
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    assert result.status == AnomalyStatus.INSUFFICIENT_DATA
    assert result.reason == "ESTIMATED_OBSERVATION_NOT_SUPPORTED"

@pytest.mark.asyncio
async def test_insufficient_quality_observation(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00)
    observation = create_observation(2.65, quality=DataQuality.INSUFFICIENT)
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    assert result.status == AnomalyStatus.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_entity_isolation(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00, entity_id="TRK-A")
    observation = create_observation(2.65, entity_id="TRK-B")
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    assert result.status == AnomalyStatus.INSUFFICIENT_DATA
    assert result.reason == "ENTITY_MISMATCH"

@pytest.mark.asyncio
async def test_metric_isolation(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00, metric_type=FuelMetricType.FUEL_CONSUMPTION)
    observation = create_observation(2.65, metric_type=FuelMetricType.FUEL_EFFICIENCY)
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    # Actually, if current obs is not EFFICIENCY, it fails early.
    # So let's make observation EFFICIENCY, baseline CONSUMPTION.
    # Observation will pass the EFFICIENCY check, then fail on metric isolation.
    assert result.status == AnomalyStatus.INSUFFICIENT_DATA
    assert result.reason == "METRIC_MISMATCH"

@pytest.mark.asyncio
async def test_idempotency_upsert(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00)
    observation = create_observation(2.65, obs_id=999)
    
    # Process it twice
    await engine.detect_anomaly(uow, observation, baseline)
    await engine.detect_anomaly(uow, observation, baseline)
    
    assert len(uow.repositories.fuel_anomaly.anomalies) == 1
    assert uow.repositories.fuel_anomaly.anomalies[0].observation_reference == "999"

@pytest.mark.asyncio
async def test_traceability(engine):
    uow = MockUOW()
    baseline = create_baseline(3.00, baseline_id=456)
    observation = create_observation(2.65, obs_id=123)
    
    result = await engine.detect_anomaly(uow, observation, baseline)
    
    assert result.observation_reference == "123"
    assert result.baseline_reference == "456"
    
    saved_anomaly = uow.repositories.fuel_anomaly.anomalies[0]
    assert saved_anomaly.observation_reference == "123"
    assert saved_anomaly.baseline_reference == "456"
