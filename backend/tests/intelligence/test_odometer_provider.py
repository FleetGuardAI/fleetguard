import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from infrastructure.intelligence.fuel_domain.metrics.schemas import (
    NormalizedFuelMetric, 
    MetricCalculationResult,
    FuelSource,
    DataQuality,
    MeasurementType,
    FuelMetricType,
    EntityTypeEnum,
)
from infrastructure.intelligence.fuel_domain.metrics.odometer_provider import OdometerFuelProvider
from models.operational_event import EventType, EntityType, OperationalEvent


def create_mock_event(event_id, occurred_at, payload):
    return OperationalEvent(
        id=event_id,
        event_type=EventType.FUEL_FILLED,
        entity_type=EntityType.VEHICLE,
        entity_id="TRK-123",
        occurred_at=occurred_at,
        payload=payload
    )


@pytest.fixture
def mock_uow():
    return AsyncMock()


@pytest.mark.asyncio
async def test_full_tank_to_full_tank(mock_uow):
    provider = OdometerFuelProvider()
    
    t1 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 2, tzinfo=timezone.utc)
    
    events = [
        create_mock_event("uuid-1", t1, {"liters": 150, "odometer_km": 100000, "is_full_tank": True}),
        create_mock_event("uuid-2", t2, {"liters": 170, "odometer_km": 100500, "is_full_tank": True})
    ]
    
    mock_uow.repositories.operational_event.list_events_by_entity.return_value = events
    
    result = await provider.calculate_fuel_efficiency(
        uow=mock_uow,
        entity_id="TRK-123",
        entity_type=EntityTypeEnum.TRUCK,
        period_start=t1,
        period_end=t2
    )
    
    assert result.status == "SUCCESS"
    assert result.metric is not None
    # distance = 500, fuel = 170 -> 500/170 = 2.941...
    assert abs(result.metric.value - (500 / 170)) < 0.001
    assert result.metric.source == FuelSource.MANUAL_ENTRY
    assert result.metric.measurement_type == MeasurementType.DERIVED
    assert result.metric.quality == DataQuality.MEDIUM


@pytest.mark.asyncio
async def test_partial_refill_isolation(mock_uow):
    provider = OdometerFuelProvider()
    
    t1 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 2, tzinfo=timezone.utc)
    t3 = datetime(2026, 8, 3, tzinfo=timezone.utc)
    
    events = [
        create_mock_event("uuid-1", t1, {"liters": 150, "odometer_km": 100000, "is_full_tank": True}),
        create_mock_event("uuid-2", t2, {"liters": 50, "odometer_km": 100200, "is_full_tank": False}),
        create_mock_event("uuid-3", t3, {"liters": 120, "odometer_km": 100500, "is_full_tank": True})
    ]
    
    mock_uow.repositories.operational_event.list_events_by_entity.return_value = events
    
    result = await provider.calculate_fuel_efficiency(
        uow=mock_uow,
        entity_id="TRK-123",
        entity_type=EntityTypeEnum.TRUCK,
        period_start=t1,
        period_end=t3
    )
    
    assert result.status == "SUCCESS"
    assert result.metric is not None
    # distance = 500. Fuel consumed = 50 + 120 = 170.
    assert abs(result.metric.value - (500 / 170)) < 0.001


@pytest.mark.asyncio
async def test_odometer_regression_rejected(mock_uow):
    provider = OdometerFuelProvider()
    
    t1 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 2, tzinfo=timezone.utc)
    
    events = [
        create_mock_event("uuid-1", t1, {"liters": 150, "odometer_km": 100500, "is_full_tank": True}),
        create_mock_event("uuid-2", t2, {"liters": 170, "odometer_km": 100000, "is_full_tank": True})
    ]
    
    mock_uow.repositories.operational_event.list_events_by_entity.return_value = events
    
    result = await provider.calculate_fuel_efficiency(
        uow=mock_uow,
        entity_id="TRK-123",
        entity_type=EntityTypeEnum.TRUCK,
        period_start=t1,
        period_end=t2
    )
    
    assert result.status == "INVALID_DATA"
    assert result.metric is None


@pytest.mark.asyncio
async def test_zero_fuel_rejected(mock_uow):
    provider = OdometerFuelProvider()
    
    t1 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 2, tzinfo=timezone.utc)
    
    events = [
        create_mock_event("uuid-1", t1, {"liters": 150, "odometer_km": 100000, "is_full_tank": True}),
        create_mock_event("uuid-2", t2, {"liters": 0, "odometer_km": 100500, "is_full_tank": True})
    ]
    
    mock_uow.repositories.operational_event.list_events_by_entity.return_value = events
    
    result = await provider.calculate_fuel_efficiency(
        uow=mock_uow,
        entity_id="TRK-123",
        entity_type=EntityTypeEnum.TRUCK,
        period_start=t1,
        period_end=t2
    )
    
    assert result.status == "INVALID_DATA"
    assert "ZERO" in result.reason
    assert result.metric is None


@pytest.mark.asyncio
async def test_full_tank_state_check(mock_uow):
    provider = OdometerFuelProvider()
    
    t1 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 2, tzinfo=timezone.utc)
    
    events = [
        create_mock_event("uuid-1", t1, {"liters": 150, "odometer_km": 100000, "is_full_tank": True}),
        create_mock_event("uuid-2", t2, {"liters": 170, "odometer_km": 100500, "is_full_tank": False})
    ]
    
    mock_uow.repositories.operational_event.list_events_by_entity.return_value = events
    
    result = await provider.calculate_fuel_efficiency(
        uow=mock_uow,
        entity_id="TRK-123",
        entity_type=EntityTypeEnum.TRUCK,
        period_start=t1,
        period_end=t2
    )
    
    assert result.status == "INSUFFICIENT_DATA"
    assert "BOUNDARIES_NOT_FULL_TANK" in result.reason
    assert result.metric is None
