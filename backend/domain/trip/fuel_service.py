"""
Trip Management Domain - Trip Fuel Service
Orchestrates trip fuel consumption derivation, performing strict boundary 
validation before delegating to the appropriate provider.
"""

from typing import Optional
from models.trip_domain import Trip
from domain.trip.fuel_consumption import (
    TripFuelCalculationResult,
    TripFuelConsumptionProvider,
    UnavailableTripFuelProvider
)


class TripFuelService:
    """
    Service responsible for calculating actual fuel consumption for a trip.
    Applies strict validation to trip boundaries before delegating to providers.
    """
    
    def __init__(self, provider: Optional[TripFuelConsumptionProvider] = None):
        # Default to the explicit unavailable provider to strictly prevent 
        # fake consumption from being generated.
        self._provider = provider or UnavailableTripFuelProvider()
        
    async def calculate_trip_consumption(self, trip: Trip) -> TripFuelCalculationResult:
        """
        Validates the trip's state and delegates calculation to the provider.
        Ignores planned_fuel_liters as it is not actual fuel consumed.
        """
        
        # 1. Boundary Validation
        if not trip.actual_start_time or not trip.actual_end_time:
            return TripFuelCalculationResult(
                status="INSUFFICIENT_DATA",
                reason="INVALID_TRIP_BOUNDARIES"
            )
            
        if trip.actual_start_time >= trip.actual_end_time:
            return TripFuelCalculationResult(
                status="INSUFFICIENT_DATA",
                reason="INVALID_TRIP_BOUNDARIES"
            )
            
        if trip.actual_distance is None or trip.actual_distance <= 0:
            return TripFuelCalculationResult(
                status="INSUFFICIENT_DATA",
                reason="INVALID_TRIP_BOUNDARIES"
            )
            
        # 2. Provide safely validated boundaries to the calculation provider.
        #    The provider is responsible for finding verified fuel data.
        return await self._provider.calculate(
            trip_id=str(trip.trip_id),
            vehicle_id=trip.vehicle_id,
            actual_start_time=trip.actual_start_time,
            actual_end_time=trip.actual_end_time
        )
