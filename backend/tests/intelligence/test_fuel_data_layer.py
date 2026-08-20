import pytest
from datetime import datetime, timezone
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
from infrastructure.intelligence.fuel_domain.metrics.providers import (
    FuelIntelligenceDataLayer,
    SensorFuelMetricProvider,
    TransactionFuelMetricProvider,
)
from models.derived_fuel_metrics import DerivedFuelMetric

@pytest.mark.asyncio
async def test_sensor_provider_unsupported():
    """unsupported sensor path -> no metric persisted / returns UNSUPPORTED"""
    provider = SensorFuelMetricProvider()
    uow_mock = AsyncMock()
    result = await provider.calculate_fuel_efficiency(
        uow=uow_mock,
        entity_id="TRK-123",
        entity_type=EntityTypeEnum.TRUCK,
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc)
    )
    
    assert result.status == "UNSUPPORTED"
    assert "SENSOR_SMOOTHING" in result.reason
    assert result.metric is None

@pytest.mark.asyncio
async def test_transaction_provider_unsupported():
    """unsupported transaction path -> no metric persisted / returns UNSUPPORTED"""
    provider = TransactionFuelMetricProvider()
    uow_mock = AsyncMock()
    result = await provider.calculate_fuel_efficiency(
        uow=uow_mock,
        entity_id="TRK-123",
        entity_type=EntityTypeEnum.TRUCK,
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc)
    )
    
    assert result.status == "UNSUPPORTED"
    assert "ODOMETER" in result.reason
    assert result.metric is None

@pytest.mark.asyncio
async def test_data_layer_insufficient_data():
    """missing fuel data -> INSUFFICIENT_DATA and unsupported provider cannot be selected as a valid metric"""
    uow_mock = AsyncMock()
    # Mock the odometer provider failure gracefully
    uow_mock.repositories.operational_event.list_events_by_entity.return_value = []
    
    layer = FuelIntelligenceDataLayer()
    result = await layer.get_fuel_efficiency(
        uow=uow_mock,
        entity_id="TRK-123",
        entity_type=EntityTypeEnum.TRUCK,
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc)
    )
    
    assert result.status == "INSUFFICIENT_DATA"
    assert "NO_SUPPORTED_PROVIDER" in result.reason
    assert "FUEL_SENSOR" in result.reason
    assert "MANUAL_ENTRY" in result.reason
    assert result.metric is None

def test_successful_provider_normalization():
    """successful future provider output can be normalized and traceability is preserved"""
    metric = NormalizedFuelMetric(
        entity_id="TRK-123",
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        value=3.5,
        unit="KM_PER_LITRE",
        source=FuelSource.EXTERNAL_TELEMATICS,
        quality=DataQuality.HIGH,
        measurement_type=MeasurementType.MEASURED,
        period_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 8, 2, tzinfo=timezone.utc),
        source_reference="ext_record_999"
    )
    
    assert metric.value == 3.5
    assert metric.source == FuelSource.EXTERNAL_TELEMATICS
    assert metric.quality == DataQuality.HIGH
    assert metric.measurement_type == MeasurementType.MEASURED
    assert metric.source_reference == "ext_record_999"

def test_derived_fuel_metric_model():
    """Truck A cannot affect Truck B (entity_id isolation) and source traceability is preserved on DB model"""
    db_metric = DerivedFuelMetric(
        entity_id="TRK-A",
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        value=4.0,
        unit="KM_PER_LITRE",
        source=FuelSource.FUEL_TRANSACTION,
        quality=DataQuality.MEDIUM,
        measurement_type=MeasurementType.DERIVED,
        period_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 8, 2, tzinfo=timezone.utc),
        source_reference="tx_123"
    )
    
    assert db_metric.entity_id == "TRK-A"
    assert db_metric.entity_id != "TRK-B"
    assert db_metric.source == FuelSource.FUEL_TRANSACTION
    assert db_metric.measurement_type == MeasurementType.DERIVED
