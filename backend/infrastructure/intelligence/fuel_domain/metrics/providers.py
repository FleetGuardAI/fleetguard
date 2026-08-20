"""
FleetGuard — Fuel Intelligence Metric Providers
Orchestrates the evaluation of different operational data sources 
to produce a NormalizedFuelMetric.
"""

from typing import List, Optional
import abc
from datetime import datetime

from infrastructure.intelligence.fuel_domain.metrics.schemas import (
    NormalizedFuelMetric, 
    MetricCalculationResult,
    FuelSource,
    DataQuality,
    MeasurementType,
    FuelMetricType,
    EntityTypeEnum,
)
from infrastructure.uow import AbstractUnitOfWork

class BaseFuelMetricProvider(abc.ABC):
    """
    Abstract base class for all fuel metric providers.
    """
    
    @property
    @abc.abstractmethod
    def source(self) -> FuelSource:
        pass

    @abc.abstractmethod
    async def calculate_fuel_efficiency(
        self,
        uow: AbstractUnitOfWork,
        entity_id: str, 
        entity_type: EntityTypeEnum, 
        period_start: datetime, 
        period_end: datetime
    ) -> MetricCalculationResult:
        """
        Attempts to calculate fuel efficiency for the given entity and period.
        """
        pass


class SensorFuelMetricProvider(BaseFuelMetricProvider):
    """
    Provider that attempts to use FuelLog telemetry.
    """
    
    @property
    def source(self) -> FuelSource:
        return FuelSource.FUEL_SENSOR

    async def calculate_fuel_efficiency(
        self,
        uow: AbstractUnitOfWork,
        entity_id: str, 
        entity_type: EntityTypeEnum, 
        period_start: datetime, 
        period_end: datetime
    ) -> MetricCalculationResult:
        
        # Current system lacks EMA smoothing and automatic event detection.
        # Producing a metric from raw data would violate financial intelligence integrity.
        return MetricCalculationResult(
            status="UNSUPPORTED",
            reason="SENSOR_SMOOTHING_AND_EVENT_DETECTION_NOT_IMPLEMENTED"
        )


class TransactionFuelMetricProvider(BaseFuelMetricProvider):
    """
    Provider that attempts to use FuelTransaction (MANUAL_ENTRY or similar).
    """
    
    @property
    def source(self) -> FuelSource:
        return FuelSource.MANUAL_ENTRY

    async def calculate_fuel_efficiency(
        self,
        uow: AbstractUnitOfWork,
        entity_id: str, 
        entity_type: EntityTypeEnum, 
        period_start: datetime, 
        period_end: datetime
    ) -> MetricCalculationResult:
        
        # Current database does not have an odometer field, making exact distance mapping impossible.
        return MetricCalculationResult(
            status="UNSUPPORTED",
            reason="ODOMETER_AND_TRIP_ASSOCIATION_UNAVAILABLE"
        )


class FuelIntelligenceDataLayer:
    """
    Orchestrator that queries all available providers and selects the best
    supported and successful metric.
    """
    def __init__(self):
        from infrastructure.intelligence.fuel_domain.metrics.odometer_provider import OdometerFuelProvider
        
        self._providers: List[BaseFuelMetricProvider] = [
            OdometerFuelProvider(),
            SensorFuelMetricProvider(),
            TransactionFuelMetricProvider(),
        ]

    async def get_fuel_efficiency(
        self,
        uow: AbstractUnitOfWork,
        entity_id: str, 
        entity_type: EntityTypeEnum, 
        period_start: datetime, 
        period_end: datetime
    ) -> MetricCalculationResult:
        """
        Iterates through providers to find a successful calculation.
        If none succeed, returns INSUFFICIENT_DATA with details of the failures.
        """
        reasons = []
        
        for provider in self._providers:
            result = await provider.calculate_fuel_efficiency(
                uow=uow,
                entity_id=entity_id,
                entity_type=entity_type,
                period_start=period_start,
                period_end=period_end
            )
            
            if result.status == "SUCCESS" and result.metric is not None:
                return result
                
            reasons.append(f"{provider.source.value}: {result.reason}")
            
        # None succeeded. Combine the reasons.
        combined_reasons = " | ".join(reasons)
        return MetricCalculationResult(
            status="INSUFFICIENT_DATA",
            reason=f"NO_SUPPORTED_PROVIDER: {combined_reasons}"
        )
