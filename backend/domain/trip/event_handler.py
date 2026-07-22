"""
Trip Management Domain - Event Handler
Subscribes to Operational Events and translates them into Trip domain commands.
"""

import logging
from typing import Any, Optional
import uuid

from domain.trip.service import TripService
from domain.trip.value_objects import Location
from models.operational_event import EventType

logger = logging.getLogger(__name__)

class TripEventHandler:
    """
    Subscribes to Operational Events to drive the Trip lifecycle.
    """
    def __init__(self, trip_service: TripService):
        self.trip_service = trip_service

    async def handle_event(self, event: Any) -> None:
        """
        Main entry point for handling an OperationalEvent.
        """
        # We assume `event` is a parsed OperationalEventResponse schema from the processor
        event_type_str = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        
        if event_type_str == EventType.IGNITION_STARTED.value:
            await self._handle_ignition_started(event)
        elif event_type_str == EventType.IGNITION_STOPPED.value:
            await self._handle_ignition_stopped(event)
        elif event_type_str == EventType.POSITION_RECORDED.value:
            await self._handle_position_recorded(event)
        else:
            logger.debug(f"Event {event_type_str} ignored by TripEventHandler.")

    async def _handle_ignition_started(self, event: Any) -> None:
        payload = event.payload or {}
        location_data = payload.get("location", {})
        
        location = Location(
            latitude=location_data.get("latitude", 0.0),
            longitude=location_data.get("longitude", 0.0)
        )
        
        # In a real system, the event processor or this handler would lookup the active driver assignment
        # For this implementation, we extract from payload or mock.
        driver_assignment_id_str = payload.get("driver_assignment_id")
        driver_assignment_id = uuid.UUID(driver_assignment_id_str) if driver_assignment_id_str else None
        
        # We assume the event payload contains the organization ID
        organization_id = uuid.UUID(payload.get("organization_id", str(uuid.uuid4())))
        
        vehicle_id = event.entity_id
        
        try:
            self.trip_service.handle_ignition_started(
                organization_id=organization_id,
                vehicle_id=vehicle_id,
                location=location,
                driver_assignment_id=driver_assignment_id
            )
            logger.info(f"Trip started for vehicle {vehicle_id}")
        except Exception as e:
            logger.error(f"Failed to start trip for vehicle {vehicle_id}: {e}")

    async def _handle_ignition_stopped(self, event: Any) -> None:
        payload = event.payload or {}
        location_data = payload.get("location", {})
        
        location = Location(
            latitude=location_data.get("latitude", 0.0),
            longitude=location_data.get("longitude", 0.0)
        )
        
        vehicle_id = event.entity_id
        
        try:
            self.trip_service.handle_ignition_stopped(
                vehicle_id=vehicle_id,
                location=location
            )
            logger.info(f"Trip completed for vehicle {vehicle_id}")
        except Exception as e:
            logger.error(f"Failed to complete trip for vehicle {vehicle_id}: {e}")

    async def _handle_position_recorded(self, event: Any) -> None:
        """
        Updates distance and metrics for active trips based on GPS pings.
        """
        vehicle_id = event.entity_id
        trip = self.trip_service._repository.find_active_trip_for_vehicle(vehicle_id)
        if trip:
            # Here we would update distance, add waypoints, etc.
            # Omitted for brevity in this architectural pass.
            logger.debug(f"Position recorded for active trip {trip.trip_id}")
