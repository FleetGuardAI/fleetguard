import pytest
from datetime import datetime, timezone, timedelta
import math

from models.derived_fuel_metrics import DerivedFuelMetric, EntityTypeEnum, FuelMetricType, DataQuality, MeasurementType, FuelSource
from models.entity_baseline import EntityBaseline, BaselineStatus
from infrastructure.intelligence.fuel_domain.baseline.engine import FuelBaselineEngine

class MockDerivedFuelMetricRepository:
    def __init__(self, metrics):
        self.metrics = metrics

    async def get_historical_observations(self, entity_id, entity_type, metric_type, period_start, period_end):
        return [
            m for m in self.metrics 
            if m.entity_id == entity_id 
            and m.entity_type == entity_type 
            and m.metric_type == metric_type
            and m.period_start >= period_start 
            and m.period_end <= period_end
        ]

class MockEntityBaselineRepository:
    def __init__(self):
        self.baselines = []

    async def upsert_baseline(self, baseline):
        self.baselines.append(baseline)
        return baseline

class MockUOW:
    def __init__(self, metrics):
        self.repositories = type('Repositories', (), {
            'derived_fuel_metric': MockDerivedFuelMetricRepository(metrics),
            'entity_baseline': MockEntityBaselineRepository()
        })()

def create_metric(
    value, 
    quality=DataQuality.HIGH, 
    measurement_type=MeasurementType.DERIVED, 
    entity_id="TRK-1", 
    metric_type=FuelMetricType.FUEL_EFFICIENCY,
    entity_type=EntityTypeEnum.TRUCK,
    t_offset=0
):
    base_time = datetime(2026, 8, 1, tzinfo=timezone.utc)
    return DerivedFuelMetric(
        entity_id=entity_id,
        entity_type=entity_type,
        metric_type=metric_type,
        value=value,
        unit="KM_PER_LITRE",
        source=FuelSource.ODOMETER_FUEL,
        quality=quality,
        measurement_type=measurement_type,
        period_start=base_time + timedelta(days=t_offset),
        period_end=base_time + timedelta(days=t_offset+1),
        sample_size=1
    )

@pytest.fixture
def engine():
    return FuelBaselineEngine()

@pytest.mark.asyncio
async def test_normal_baseline(engine):
    # Values: 2.94, 3.10, 2.98, 3.05, 2.91. Median is 2.98
    metrics = [
        create_metric(2.94, t_offset=1),
        create_metric(3.10, t_offset=2),
        create_metric(2.98, t_offset=3),
        create_metric(3.05, t_offset=4),
        create_metric(2.91, t_offset=5),
    ]
    uow = MockUOW(metrics)
    
    result = await engine.calculate_baseline(
        uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
        datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc)
    )
    
    assert result.status == BaselineStatus.VALID
    assert result.baseline_value == 2.98
    assert result.sample_size == 5
    assert result.data_quality == DataQuality.HIGH
    assert len(uow.repositories.entity_baseline.baselines) == 1

@pytest.mark.asyncio
async def test_outlier_resistance(engine):
    # Values: 2.9, 3.0, 3.1, 3.0, 6.8. Median is 3.0
    metrics = [
        create_metric(2.9),
        create_metric(3.0),
        create_metric(3.1),
        create_metric(3.0),
        create_metric(6.8),
    ]
    uow = MockUOW(metrics)
    
    result = await engine.calculate_baseline(
        uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
        datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc)
    )
    
    assert result.status == BaselineStatus.VALID
    assert result.baseline_value == 3.0

@pytest.mark.asyncio
async def test_insufficient_samples(engine):
    metrics = [create_metric(2.9)] * 4
    uow = MockUOW(metrics)
    
    result = await engine.calculate_baseline(
        uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
        datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc)
    )
    
    assert result.status == BaselineStatus.INSUFFICIENT_DATA
    assert result.reason == "INSUFFICIENT_BASELINE_SAMPLES"
    assert result.baseline_value is None
    assert len(uow.repositories.entity_baseline.baselines) == 0

@pytest.mark.asyncio
async def test_estimated_exclusion(engine):
    metrics = [create_metric(2.9)] * 4 + [create_metric(3.0, measurement_type=MeasurementType.ESTIMATED)]
    uow = MockUOW(metrics)
    
    result = await engine.calculate_baseline(
        uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
        datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc)
    )
    
    # 4 valid + 1 estimated = 4 valid, which is < 5
    assert result.status == BaselineStatus.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_insufficient_quality_exclusion(engine):
    metrics = [create_metric(2.9)] * 4 + [create_metric(3.0, quality=DataQuality.INSUFFICIENT)]
    uow = MockUOW(metrics)
    
    result = await engine.calculate_baseline(
        uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
        datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc)
    )
    
    assert result.status == BaselineStatus.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_invalid_values(engine):
    invalid_values = [0, -1.0, math.nan, math.inf, -math.inf, None]
    
    for val in invalid_values:
        metrics = [create_metric(2.9)] * 4 + [create_metric(val)]
        uow = MockUOW(metrics)
        
        result = await engine.calculate_baseline(
            uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
            datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc)
        )
        assert result.status == BaselineStatus.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_medium_quality(engine):
    metrics = [create_metric(2.9, quality=DataQuality.MEDIUM)] * 5
    uow = MockUOW(metrics)
    
    result = await engine.calculate_baseline(
        uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
        datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc)
    )
    
    assert result.status == BaselineStatus.VALID
    assert result.data_quality == DataQuality.MEDIUM

@pytest.mark.asyncio
async def test_entity_isolation(engine):
    metrics = [create_metric(2.9, entity_id="TRK-1")] * 4 + [create_metric(3.0, entity_id="TRK-2")]
    uow = MockUOW(metrics)
    
    result = await engine.calculate_baseline(
        uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
        datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc)
    )
    
    assert result.status == BaselineStatus.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_metric_isolation(engine):
    metrics = [create_metric(2.9, metric_type=FuelMetricType.FUEL_EFFICIENCY)] * 4 + [create_metric(3.0, metric_type=FuelMetricType.FUEL_CONSUMPTION)]
    uow = MockUOW(metrics)
    
    result = await engine.calculate_baseline(
        uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
        datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc)
    )
    
    assert result.status == BaselineStatus.INSUFFICIENT_DATA

@pytest.mark.asyncio
async def test_date_filtering(engine):
    # Create 4 inside the period, 1 outside the period
    metrics = [
        create_metric(2.9, t_offset=1),
        create_metric(2.9, t_offset=2),
        create_metric(2.9, t_offset=3),
        create_metric(2.9, t_offset=4),
        create_metric(2.9, t_offset=10), # outside period
    ]
    uow = MockUOW(metrics)
    
    base_time = datetime(2026, 8, 1, tzinfo=timezone.utc)
    
    result = await engine.calculate_baseline(
        uow, "TRK-1", EntityTypeEnum.TRUCK, FuelMetricType.FUEL_EFFICIENCY, 
        base_time, base_time + timedelta(days=5) # Ends at offset 5
    )
    
    assert result.status == BaselineStatus.INSUFFICIENT_DATA
