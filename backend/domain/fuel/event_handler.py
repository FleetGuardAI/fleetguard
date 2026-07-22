"""
Fuel Operations Domain - Event Handler
"""

import logging
import uuid
from typing import Any

from domain.fuel.service import FuelService
from domain.fuel.value_objects import Location
from models.operational_event import EventType

logger = logging.getLogger(__name__)

class FuelEventHandler:
    """
    Subscribes to Operational Events and Domain Events to drive the Fuel Ledger.
    """
    def __init__(self, fuel_service: FuelService):
        self.fuel_service = fuel_service
        # In a real implementation, we would inject query services here to resolve
        # driver_id and trip_id. For brevity, we assume payload passes them if known.

    async def handle_event(self, event: Any) -> None:
        event_type_str = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        
        if event_type_str == EventType.FUEL_FILLED.value:
            await self._handle_fill(event)
        elif event_type_str == EventType.FUEL_DRAINED.value:
            await self._handle_drain(event)
        else:
            logger.debug(f"Event {event_type_str} ignored by FuelEventHandler.")

    async def _handle_fill(self, event: Any) -> None:
        payload = event.payload or {}
        liters = payload.get("liters", 0.0)
        
        loc_data = payload.get("location")
        location = Location(latitude=loc_data["latitude"], longitude=loc_data["longitude"]) if loc_data else None
        
        # Mocks of lookups to Trip/Assignment domains
        driver_str = payload.get("driver_assignment_id")
        driver_id = uuid.UUID(driver_str) if driver_str else None
        
        trip_str = payload.get("trip_id")
        trip_id = uuid.UUID(trip_str) if trip_str else None

        vehicle_id = event.entity_id
        
        try:
            self.fuel_service.handle_fuel_fill(vehicle_id, liters, driver_id, trip_id, location)
            logger.info(f"Recorded fill for vehicle {vehicle_id}: {liters}L")
        except Exception as e:
            logger.error(f"Failed to record fill for {vehicle_id}: {e}")

    async def _handle_drain(self, event: Any) -> None:
        payload = event.payload or {}
        liters = payload.get("liters", 0.0)
        
        loc_data = payload.get("location")
        location = Location(latitude=loc_data["latitude"], longitude=loc_data["longitude"]) if loc_data else None
        
        driver_str = payload.get("driver_assignment_id")
        driver_id = uuid.UUID(driver_str) if driver_str else None
        
        trip_str = payload.get("trip_id")
        trip_id = uuid.UUID(trip_str) if trip_str else None

        vehicle_id = event.entity_id
        
        try:
            self.fuel_service.handle_fuel_drain(vehicle_id, liters, driver_id, trip_id, location)
            logger.info(f"Recorded drain for vehicle {vehicle_id}: {liters}L")
        except Exception as e:
            logger.error(f"Failed to record drain for {vehicle_id}: {e}")
