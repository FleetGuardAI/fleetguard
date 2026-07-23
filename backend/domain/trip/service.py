"""
Trip Management Domain - Service
"""

import uuid
from typing import Optional

from domain.trip.models import Trip, TripStatus
from domain.trip.value_objects import Location
from domain.trip.aggregate import TripAggregate
from domain.trip.repository import BaseTripRepository
from domain.trip.errors import TripNotFound, InvalidTripState


class TripService:
    """
    Application service orchestrating the Trip domain.
    Invoked exclusively by the Operational Event Handler.
    """

    def __init__(self, repository: BaseTripRepository):
        self._repository = repository

    def handle_ignition_started(self, organization_id: uuid.UUID, vehicle_id: str, location: Location, driver_assignment_id: Optional[uuid.UUID] = None) -> Trip:
        """
        Creates and starts a trip when ignition is detected.
        """
        existing_trip = self._repository.find_active_trip_for_vehicle(vehicle_id)
        if existing_trip:
            # If already active, we might just return it, or handle edge cases.
            return existing_trip

        trip = Trip(
            organization_id=organization_id,
            vehicle_id=vehicle_id
        )
        
        created_trip, create_events = TripAggregate.create_trip(trip)
        self._repository.create(created_trip)
        
        started_trip, start_events = TripAggregate.start_trip(created_trip, location, driver_assignment_id)
        self._repository.update(started_trip)
        
        # Publish events via EventBus omitted for simplicity
        
        return started_trip

    def handle_ignition_stopped(self, vehicle_id: str, location: Location) -> Optional[Trip]:
        """
        Completes a trip when ignition stops.
        """
        trip = self._repository.find_active_trip_for_vehicle(vehicle_id)
        if not trip:
            return None
            
        completed_trip, events = TripAggregate.complete_trip(trip, location)
        self._repository.update(completed_trip)
        
        return completed_trip

    def get_trip(self, trip_id: uuid.UUID) -> Trip:
        trip = self._repository.find_by_id(trip_id)
        if not trip:
            raise TripNotFound(f"Trip {trip_id} not found.")
        return trip
