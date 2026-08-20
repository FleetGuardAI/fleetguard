import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from models.operational_event import EventType
from models.trip_domain import Trip, TripStatus
from models.vehicle_domain import Vehicle
from models.derived_fuel_metrics import DerivedFuelMetric, EntityTypeEnum, FuelMetricType, DataQuality, MeasurementType, FuelSource
from models.entity_baseline import EntityBaseline, BaselineStatus
from models.fuel_anomaly import FuelAnomaly, AnomalyDirection, AnomalySeverity, AnomalyStatus
from models.fuel_financial_impact import FuelFinancialImpact, FuelPriceSource

from infrastructure.intelligence.fuel_domain.orchestrator import FuelIntelligenceOrchestrator
from infrastructure.intelligence.fuel_domain.metrics.schemas import MetricCalculationResult
from infrastructure.intelligence.fuel_domain.baseline.schemas import BaselineResult
from infrastructure.intelligence.fuel_domain.anomaly.schemas import FuelAnomalyResult
from infrastructure.intelligence.fuel_domain.financial.schemas import FuelFinancialImpactResult
from infrastructure.intelligence.fuel_domain.root_cause.schemas import RootCauseAnalysisResult

@pytest.mark.asyncio
async def test_orchestrator_ignores_invalid_events():
    orchestrator = FuelIntelligenceOrchestrator()
    uow = AsyncMock()
    
    # Send a non-trigger event
    await orchestrator.execute_from_event(
        uow=uow,
        event_type=EventType.TRIP_STARTED,
        entity_id="TRK123",
        payload={},
        occurred_at=datetime.now(timezone.utc)
    )
    
    # The UoW should not have been queried for trip processing
    uow.repositories.trip.get_trip_by_business_id.assert_not_called()

@pytest.mark.asyncio
async def test_orchestrator_trip_completed_success_path():
    orchestrator = FuelIntelligenceOrchestrator()
    fuel_handler = orchestrator._registry._handlers[0]
    
    # Mock Engines
    fuel_handler.data_layer = AsyncMock()
    fuel_handler.baseline_engine = AsyncMock()
    fuel_handler.anomaly_engine = AsyncMock()
    fuel_handler.financial_engine = AsyncMock()
    fuel_handler.root_cause_engine = AsyncMock()
    
    uow = AsyncMock()
    
    # Mock Trip
    vehicle = Vehicle(id=1, registration_number="MH12AB1234")
    trip = Trip(
        trip_id="TRIP-1",
        status=TripStatus.COMPLETED,
        actual_start_time=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        actual_end_time=datetime(2023, 1, 1, 14, 0, tzinfo=timezone.utc),
        vehicle=vehicle
    )
    uow.repositories.trip.get_trip_by_business_id.return_value = trip
    
    # 1. Observation
    from infrastructure.intelligence.fuel_domain.metrics.schemas import NormalizedFuelMetric
    metric = NormalizedFuelMetric(
        source_reference="uuid1,uuid2",
        value=2.0,
        quality=DataQuality.HIGH,
        period_start=trip.actual_start_time,
        period_end=trip.actual_end_time,
        sample_size=1,
        entity_id=vehicle.registration_number,
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        unit="KM_PER_LITRE",
        source=FuelSource.ODOMETER_FUEL,
        measurement_type=MeasurementType.DERIVED
    )
    fuel_handler.data_layer.get_fuel_efficiency.return_value = MetricCalculationResult(
        status="SUCCESS",
        metric=metric
    )
    
    # Mock Idempotency Check (Metric does not exist)
    uow.repositories.derived_fuel_metric.get_by_source_reference.return_value = None
    uow.repositories.derived_fuel_metric.upsert_metric.return_value = metric
    
    # 2. Baseline
    baseline = EntityBaseline(
        baseline_value=3.0,
        status=BaselineStatus.VALID,
        period_start=datetime(2022, 10, 1, tzinfo=timezone.utc),
        period_end=trip.actual_start_time
    )
    fuel_handler.baseline_engine.calculate_baseline.return_value = BaselineResult(
        status=BaselineStatus.VALID,
        entity_id=vehicle.registration_number,
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        baseline_value=3.0,
        unit="KM_PER_LITRE",
        sample_size=10,
        calculation_method="MEDIAN",
        data_quality=DataQuality.HIGH,
        period_start=datetime(2022, 10, 1, tzinfo=timezone.utc),
        period_end=trip.actual_start_time
    )
    uow.repositories.entity_baseline.get_baseline.return_value = baseline
    
    # 3. Anomaly
    anomaly = FuelAnomaly(
        observation_reference="uuid1,uuid2",
        status=AnomalyStatus.ANOMALY,
        direction=AnomalyDirection.DEGRADATION,
        entity_id=vehicle.registration_number,
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        baseline_value=3.0,
        observed_value=2.0,
        deviation_percent=-33.33,
        severity=AnomalySeverity.CRITICAL,
        baseline_reference="base1",
        period_start=trip.actual_start_time,
        period_end=trip.actual_end_time,
        detected_at=datetime.now(timezone.utc)
    )
    fuel_handler.anomaly_engine.detect_anomaly.return_value = FuelAnomalyResult(
        status=AnomalyStatus.ANOMALY,
        direction=AnomalyDirection.DEGRADATION,
        entity_id=vehicle.registration_number,
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        baseline_value=3.0,
        observed_value=2.0,
        deviation_percent=-33.33,
        severity=AnomalySeverity.CRITICAL,
        baseline_reference="base1",
        observation_reference="uuid1,uuid2",
        detected_at=datetime.now(timezone.utc),
        period_start=trip.actual_start_time,
        period_end=trip.actual_end_time
    )
    uow.repositories.fuel_anomaly.get_by_observation.return_value = anomaly
    
    # 4. Financial Impact
    impact = FuelFinancialImpact(
        anomaly_reference="uuid1,uuid2",
        estimated_financial_exposure=5000.0,
        entity_id=vehicle.registration_number,
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        baseline_efficiency=3.0,
        observed_efficiency=2.0,
        distance=500.0,
        expected_fuel_liters=166.6,
        implied_fuel_liters=250.0,
        excess_fuel_liters=83.4,
        fuel_price_per_liter=60.0,
        fuel_price_source=FuelPriceSource.ACTUAL_PURCHASE_PRICE,
        baseline_reference="base1",
        observation_reference="uuid1,uuid2",
        period_start=trip.actual_start_time,
        period_end=trip.actual_end_time,
        calculation_method="BASELINE_VS_OBSERVED_EFFICIENCY"
    )
    fuel_handler.financial_engine.calculate_financial_impact.return_value = FuelFinancialImpactResult(
        status="SUCCESS",
        estimated_financial_exposure=5000.0,
        entity_id=vehicle.registration_number,
        entity_type=EntityTypeEnum.TRUCK,
        metric_type=FuelMetricType.FUEL_EFFICIENCY,
        baseline_efficiency=3.0,
        observed_efficiency=2.0,
        distance=500.0,
        expected_fuel_liters=166.6,
        implied_fuel_liters=250.0,
        excess_fuel_liters=83.4,
        fuel_price_per_liter=60.0,
        fuel_price_source=FuelPriceSource.ACTUAL_PURCHASE_PRICE,
        anomaly_reference="uuid1,uuid2",
        baseline_reference="base1",
        observation_reference="uuid1,uuid2",
        period_start=trip.actual_start_time,
        period_end=trip.actual_end_time,
        calculation_method="BASELINE_VS_OBSERVED_EFFICIENCY"
    )
    uow.repositories.fuel_financial_impact.get_by_anomaly.return_value = impact
    
    # 5. Root Cause
    fuel_handler.root_cause_engine.analyze_root_cause.return_value = RootCauseAnalysisResult(
        status="SUCCESS",
        entity_id=vehicle.registration_number,
        entity_type=EntityTypeEnum.TRUCK,
        anomaly_reference="uuid1,uuid2",
        financial_impact_reference="uuid1,uuid2",
        period_start=trip.actual_start_time,
        period_end=trip.actual_end_time,
        candidate_causes=[]
    )
    
    await orchestrator.execute_from_event(
        uow=uow,
        event_type=EventType.TRIP_COMPLETED,
        entity_id="TRIP-1",
        payload={},
        occurred_at=datetime.now(timezone.utc)
    )
    
    # Verify the cascade execution
    fuel_handler.data_layer.get_fuel_efficiency.assert_called_once()
    fuel_handler.baseline_engine.calculate_baseline.assert_called_once()
    fuel_handler.anomaly_engine.detect_anomaly.assert_called_once()
    fuel_handler.financial_engine.calculate_financial_impact.assert_called_once()
    fuel_handler.root_cause_engine.analyze_root_cause.assert_called_once()
