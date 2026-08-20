"""
FleetGuard — Full-Tank Odometer Fuel Provider
Produces derived fuel efficiency metrics by analyzing bounding full-tank 
operational events (FUEL_FILLED) for a given vehicle within a period.
"""

from typing import List, Optional
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
from infrastructure.intelligence.fuel_domain.metrics.providers import BaseFuelMetricProvider
from models.operational_event import EventType, EntityType
from infrastructure.uow import AbstractUnitOfWork

class OdometerFuelProvider(BaseFuelMetricProvider):
    """
    Provider that uses the Full-Tank method via FUEL_FILLED operational events.
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
        
        if entity_type != EntityTypeEnum.TRUCK:
            return MetricCalculationResult(
                status="UNSUPPORTED",
                reason="ODOMETER_PROVIDER_ONLY_SUPPORTS_TRUCK_ENTITY"
            )
            
        # 1. Query FUEL_FILLED events for this vehicle within the period
        events = await uow.repositories.operational_event.list_events_by_entity(
            entity_type=EntityType.VEHICLE,
            entity_id=entity_id,
            limit=500
        )
        
        # Filter for FUEL_FILLED events strictly within period_start and period_end
        fuel_events = [
            e for e in events 
            if e.event_type == EventType.FUEL_FILLED 
            and period_start <= e.occurred_at <= period_end
        ]
        
        # Sort chronologically
        fuel_events.sort(key=lambda e: e.occurred_at)
        
        if len(fuel_events) < 2:
            return MetricCalculationResult(
                status="INSUFFICIENT_DATA",
                reason="REQUIRES_AT_LEAST_TWO_FUEL_EVENTS"
            )
            
        # 2. Find valid full-tank boundaries
        # For Milestone 1C, we look for two bounding full-tank events that encompass
        # the entire set of events, or at least consecutive full-tank events.
        # If there are any partial fills, they must be properly accounted for.
        # To strictly avoid corrupting metrics, we only calculate if ALL events in the 
        # interval between the two boundaries are valid.
        
        # For simplicity in this foundational milestone, we evaluate if the FIRST and LAST 
        # events in the given period are full-tank events.
        first_event = fuel_events[0]
        last_event = fuel_events[-1]
        
        first_payload = first_event.payload or {}
        last_payload = last_event.payload or {}
        
        if not first_payload.get("is_full_tank") or not last_payload.get("is_full_tank"):
            return MetricCalculationResult(
                status="INSUFFICIENT_DATA",
                reason="BOUNDARIES_NOT_FULL_TANK"
            )
            
        # Ensure we have odometers
        first_odo = first_payload.get("odometer_km")
        last_odo = last_payload.get("odometer_km")
        
        if first_odo is None or last_odo is None:
            return MetricCalculationResult(
                status="INSUFFICIENT_DATA",
                reason="MISSING_ODOMETER_READINGS"
            )
            
        # 3. Validate odometer regression
        distance = last_odo - first_odo
        if distance <= 0:
            return MetricCalculationResult(
                status="INVALID_DATA",
                reason="ODOMETER_REGRESSION_OR_ZERO_DISTANCE"
            )
            
        # 4. Calculate total fuel consumed
        # The fuel consumed is the sum of all fuel added AFTER the first event 
        # up to and including the last event. (The first event filled the tank, 
        # so any fuel added after it replaces what was burned).
        total_fuel = 0.0
        for i in range(1, len(fuel_events)):
            evt = fuel_events[i]
            liters = evt.payload.get("liters")
            if liters is None or liters <= 0:
                return MetricCalculationResult(
                    status="INVALID_DATA",
                    reason="ZERO_OR_MISSING_FUEL_QUANTITY"
                )
            total_fuel += liters
            
        if total_fuel <= 0:
            return MetricCalculationResult(
                status="INVALID_DATA",
                reason="NO_FUEL_CONSUMED"
            )
            
        efficiency = distance / total_fuel
        
        metric = NormalizedFuelMetric(
            entity_id=entity_id,
            entity_type=entity_type,
            metric_type=FuelMetricType.FUEL_EFFICIENCY,
            value=efficiency,
            unit="KM_PER_LITER",
            source=self.source,
            quality=DataQuality.MEDIUM, # Driver entry is MEDIUM confidence
            measurement_type=MeasurementType.DERIVED, # Explicitly derived per financial rules
            period_start=first_event.occurred_at,
            period_end=last_event.occurred_at,
            source_reference=",".join([str(e.id) for e in fuel_events])
        )
        
        return MetricCalculationResult(
            status="SUCCESS",
            metric=metric
        )
