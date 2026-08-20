"""
Trip Management Domain - Trip Fuel Consumption
Defines the domain contract for deriving actual fuel consumption for a completed trip.
"""

import abc
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from infrastructure.intelligence.fuel_domain.metrics.schemas import (
    DataQuality,
    MeasurementType,
    FuelSource,
)

class TripFuelConsumption(BaseModel):
    """
    Represents successfully calculated actual fuel consumption for a trip.
    This must NEVER be instantiated with fake or unverified data.
    """
    trip_id: str
    vehicle_id: str
    fuel_consumed_liters: float
    measurement_type: MeasurementType
    source: FuelSource
    quality: DataQuality
    period_start: datetime
    period_end: datetime
    calculation_method: str
    source_references: List[str] = Field(default_factory=list)


class TripFuelCalculationResult(BaseModel):
    """
    Structured result of a fuel consumption calculation attempt.
    status: SUCCESS, UNAVAILABLE, or INSUFFICIENT_DATA
    """
    status: str = Field(..., description="SUCCESS, UNAVAILABLE, or INSUFFICIENT_DATA")
    reason: Optional[str] = None
    metric: Optional[TripFuelConsumption] = None


class TripFuelConsumptionProvider(abc.ABC):
    """
    Abstract interface for evaluating a trip and producing TripFuelConsumption.
    """
    
    @abc.abstractmethod
    async def calculate(
        self,
        trip_id: str,
        vehicle_id: str,
        actual_start_time: datetime,
        actual_end_time: datetime
    ) -> TripFuelCalculationResult:
        """
        Attempt to calculate actual fuel consumed for the given trip boundaries.
        Must return UNAVAILABLE if the source data cannot reliably support it.
        """
        pass


class UnavailableTripFuelProvider(TripFuelConsumptionProvider):
    """
    Explicitly failing provider used when no trustworthy source exists.
    Ensures that FleetGuard does not hallucinate fuel metrics.
    """
    
    async def calculate(
        self,
        trip_id: str,
        vehicle_id: str,
        actual_start_time: datetime,
        actual_end_time: datetime
    ) -> TripFuelCalculationResult:
        
        return TripFuelCalculationResult(
            status="UNAVAILABLE",
            reason="NO_TRUSTWORTHY_FUEL_CONSUMPTION_SOURCE",
            metric=None
        )
