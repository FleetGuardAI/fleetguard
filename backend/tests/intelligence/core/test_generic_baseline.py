import pytest
import math
from datetime import datetime, timezone
from infrastructure.intelligence.core.contracts import MetricObservation
from infrastructure.intelligence.core.baseline import GenericBaselineEngine

@pytest.fixture
def baseline_engine():
    return GenericBaselineEngine()

def create_obs(value: float) -> MetricObservation:
    return MetricObservation(
        entity_id="E1",
        entity_type="TRUCK",
        metric_type="EFFICIENCY",
        value=value,
        unit="UNIT",
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc),
        source="SOURCE",
        quality="HIGH",
        measurement_type="MEASURED"
    )

def test_median_calculation(baseline_engine):
    obs = [create_obs(v) for v in [10.0, 20.0, 30.0, 40.0, 50.0]]
    assert baseline_engine.calculate_median(obs, min_samples=3) == 30.0
    
    # Even number of elements
    obs_even = [create_obs(v) for v in [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]]
    assert baseline_engine.calculate_median(obs_even, min_samples=3) == 35.0

def test_minimum_samples(baseline_engine):
    obs = [create_obs(v) for v in [10.0, 20.0]]
    assert baseline_engine.calculate_median(obs, min_samples=3) is None

def test_invalid_values(baseline_engine):
    obs = [
        create_obs(10.0),
        create_obs(20.0),
        create_obs(None),
        create_obs(float('nan')),
        create_obs(float('inf')),
        create_obs(-float('inf')),
        create_obs(30.0)
    ]
    # Only 10.0, 20.0, 30.0 are valid, len is 3. Median is 20.0
    assert baseline_engine.calculate_median(obs, min_samples=3) == 20.0

def test_outlier_resistance(baseline_engine):
    obs = [create_obs(v) for v in [10.0, 11.0, 12.0, 10.5, 1000.0]] # 1000.0 is outlier
    assert baseline_engine.calculate_median(obs, min_samples=5) == 11.0
