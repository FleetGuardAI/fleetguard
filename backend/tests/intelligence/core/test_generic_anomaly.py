import pytest
from infrastructure.intelligence.core.contracts import DirectionStrategy, SeverityStrategy, Direction, Severity, Status
from infrastructure.intelligence.core.anomaly import GenericAnomalyEngine

class MockDirectionStrategy(DirectionStrategy):
    def evaluate_direction(self, deviation_percent: float) -> Direction:
        if deviation_percent > 0:
            return Direction.IMPROVEMENT
        elif deviation_percent < 0:
            return Direction.DEGRADATION
        return Direction.NORMAL

class MockSeverityStrategy(SeverityStrategy):
    def evaluate_severity(self, deviation_percent: float) -> tuple[Severity, Status]:
        if deviation_percent <= -20.0:
            return Severity.CRITICAL, Status.ANOMALY
        elif deviation_percent <= -10.0:
            return Severity.WARNING, Status.ANOMALY
        return Severity.NORMAL, Status.NORMAL

@pytest.fixture
def anomaly_engine():
    return GenericAnomalyEngine()

@pytest.fixture
def direction_strategy():
    return MockDirectionStrategy()

@pytest.fixture
def severity_strategy():
    return MockSeverityStrategy()

def test_positive_deviation(anomaly_engine, direction_strategy, severity_strategy):
    dev, dir, sev, stat = anomaly_engine.evaluate(110.0, 100.0, direction_strategy, severity_strategy)
    assert dev == 10.0
    assert dir == Direction.IMPROVEMENT
    assert sev == Severity.NORMAL
    assert stat == Status.NORMAL

def test_negative_deviation(anomaly_engine, direction_strategy, severity_strategy):
    dev, dir, sev, stat = anomaly_engine.evaluate(85.0, 100.0, direction_strategy, severity_strategy)
    assert dev == -15.0
    assert dir == Direction.DEGRADATION
    assert sev == Severity.WARNING
    assert stat == Status.ANOMALY

def test_critical_deviation(anomaly_engine, direction_strategy, severity_strategy):
    dev, dir, sev, stat = anomaly_engine.evaluate(75.0, 100.0, direction_strategy, severity_strategy)
    assert dev == -25.0
    assert dir == Direction.DEGRADATION
    assert sev == Severity.CRITICAL
    assert stat == Status.ANOMALY

def test_zero_deviation(anomaly_engine, direction_strategy, severity_strategy):
    dev, dir, sev, stat = anomaly_engine.evaluate(100.0, 100.0, direction_strategy, severity_strategy)
    assert dev == 0.0
    assert dir == Direction.NORMAL
    assert sev == Severity.NORMAL
    assert stat == Status.NORMAL

def test_invalid_baseline(anomaly_engine, direction_strategy, severity_strategy):
    dev, dir, sev, stat = anomaly_engine.evaluate(100.0, 0.0, direction_strategy, severity_strategy)
    assert dev is None
    assert stat == Status.INSUFFICIENT_DATA
    
    dev, dir, sev, stat = anomaly_engine.evaluate(100.0, None, direction_strategy, severity_strategy)
    assert dev is None
    assert stat == Status.INSUFFICIENT_DATA

def test_invalid_observation(anomaly_engine, direction_strategy, severity_strategy):
    dev, dir, sev, stat = anomaly_engine.evaluate(float('nan'), 100.0, direction_strategy, severity_strategy)
    assert dev is None
    assert stat == Status.INSUFFICIENT_DATA

    dev, dir, sev, stat = anomaly_engine.evaluate(float('inf'), 100.0, direction_strategy, severity_strategy)
    assert dev is None
    assert stat == Status.INSUFFICIENT_DATA
