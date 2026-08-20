import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from models.trip_domain import Trip, TripStatus
from domain.trip.fuel_consumption import (
    TripFuelConsumption,
    TripFuelCalculationResult,
    TripFuelConsumptionProvider,
    UnavailableTripFuelProvider
)
from domain.trip.fuel_service import TripFuelService
from infrastructure.intelligence.fuel_domain.metrics.schemas import (
    DataQuality,
    MeasurementType,
    FuelSource,
    NormalizedFuelMetric,
    FuelMetricType,
    EntityTypeEnum
)

@pytest.fixture
def valid_trip():
    return Trip(
        trip_id="TRIP-123",
        vehicle_id="VEH-456",
        status=TripStatus.COMPLETED,
        actual_start_time=datetime.now(timezone.utc) - timedelta(hours=5),
        actual_end_time=datetime.now(timezone.utc),
        actual_distance=250.0,
        planned_fuel_liters=50.0
    )


@pytest.mark.asyncio
async def test_invalid_boundaries_missing_start_time(valid_trip):
    valid_trip.actual_start_time = None
    service = TripFuelService()
    result = await service.calculate_trip_consumption(valid_trip)
    assert result.status == "INSUFFICIENT_DATA"
    assert result.reason == "INVALID_TRIP_BOUNDARIES"


@pytest.mark.asyncio
async def test_invalid_boundaries_missing_end_time(valid_trip):
    valid_trip.actual_end_time = None
    service = TripFuelService()
    result = await service.calculate_trip_consumption(valid_trip)
    assert result.status == "INSUFFICIENT_DATA"
    assert result.reason == "INVALID_TRIP_BOUNDARIES"


@pytest.mark.asyncio
async def test_invalid_boundaries_reversed_timestamps(valid_trip):
    valid_trip.actual_start_time = valid_trip.actual_end_time + timedelta(hours=1)
    service = TripFuelService()
    result = await service.calculate_trip_consumption(valid_trip)
    assert result.status == "INSUFFICIENT_DATA"
    assert result.reason == "INVALID_TRIP_BOUNDARIES"


@pytest.mark.asyncio
async def test_invalid_boundaries_zero_distance(valid_trip):
    valid_trip.actual_distance = 0.0
    service = TripFuelService()
    result = await service.calculate_trip_consumption(valid_trip)
    assert result.status == "INSUFFICIENT_DATA"
    assert result.reason == "INVALID_TRIP_BOUNDARIES"


@pytest.mark.asyncio
async def test_valid_trip_no_fuel_source(valid_trip):
    service = TripFuelService()
    result = await service.calculate_trip_consumption(valid_trip)
    assert result.status == "UNAVAILABLE"
    assert result.reason == "NO_TRUSTWORTHY_FUEL_CONSUMPTION_SOURCE"
    assert result.metric is None


@pytest.mark.asyncio
async def test_planned_fuel_isolation(valid_trip):
    """Ensure planned fuel is completely ignored by the unavailable provider."""
    valid_trip.planned_fuel_liters = 9999.0
    service = TripFuelService()
    result = await service.calculate_trip_consumption(valid_trip)
    assert result.status == "UNAVAILABLE"
    assert result.metric is None


class MockSuccessfulProvider(TripFuelConsumptionProvider):
    async def calculate(self, trip_id: str, vehicle_id: str, actual_start_time: datetime, actual_end_time: datetime) -> TripFuelCalculationResult:
        consumption = TripFuelConsumption(
            trip_id=trip_id,
            vehicle_id=str(vehicle_id),
            fuel_consumed_liters=60.5,
            measurement_type=MeasurementType.DERIVED,
            source=FuelSource.EXTERNAL_TELEMATICS,
            quality=DataQuality.HIGH,
            period_start=actual_start_time,
            period_end=actual_end_time,
            calculation_method="MOCK_TEST",
            source_references=["evidence-1"]
        )
        return TripFuelCalculationResult(status="SUCCESS", metric=consumption)


@pytest.mark.asyncio
async def test_successful_provider_contract(valid_trip):
    service = TripFuelService(provider=MockSuccessfulProvider())
    result = await service.calculate_trip_consumption(valid_trip)
    assert result.status == "SUCCESS"
    assert result.metric is not None
    assert result.metric.fuel_consumed_liters == 60.5
    assert result.metric.trip_id == valid_trip.trip_id


def test_normalized_integration():
    """Verify that a domain metric correctly maps to NormalizedFuelMetric."""
    consumption = TripFuelConsumption(
        trip_id="TRIP-999",
        vehicle_id="VEH-999",
        fuel_consumed_liters=100.0,
        measurement_type=MeasurementType.MEASURED,
        source=FuelSource.FUEL_SENSOR,
        quality=DataQuality.HIGH,
        period_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 8, 2, tzinfo=timezone.utc),
        calculation_method="TEST_CALC",
        source_references=["doc1"]
    )
    
    normalized = NormalizedFuelMetric(
        entity_id=consumption.trip_id,
        entity_type=EntityTypeEnum.TRIP,
        metric_type=FuelMetricType.FUEL_CONSUMPTION,
        value=consumption.fuel_consumed_liters,
        unit="LITERS",
        source=consumption.source,
        quality=consumption.quality,
        measurement_type=consumption.measurement_type,
        period_start=consumption.period_start,
        period_end=consumption.period_end,
        source_reference=",".join(consumption.source_references)
    )
    
    assert normalized.value == 100.0
    assert normalized.entity_type == EntityTypeEnum.TRIP
    assert normalized.metric_type == FuelMetricType.FUEL_CONSUMPTION
    assert normalized.source == FuelSource.FUEL_SENSOR
    assert normalized.source_reference == "doc1"
