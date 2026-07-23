"""
Trip Management Domain - Aggregate Root
"""

import uuid
from typing import List, Tuple, Optional
from datetime import datetime, timezone

from domain.trip.models import Trip, TripStatus
from domain.trip.value_objects import Location
from domain.trip.events import (
    DomainEvent,
    TripCreated,
    TripStarted,
    TripPaused,
    TripResumed,
    TripCompleted,
    TripCancelled
)
from domain.trip.validators import validate_state_transition

class TripAggregate:
    """
    Enforces domain invariants and manages the state machine for a Trip.
    Driven completely by the Event Processor.
    """

    @classmethod
    def create_trip(cls, trip: Trip) -> Tuple[Trip, List[DomainEvent]]:
        if trip.status != TripStatus.CREATED:
            trip = trip.model_copy(update={"status": TripStatus.CREATED})

        event = TripCreated(
            trip_id=trip.trip_id,
            vehicle_id=trip.vehicle_id,
            organization_id=trip.organization_id
        )
        return trip, [event]

    @classmethod
    def start_trip(cls, trip: Trip, origin: Location, driver_assignment_id: Optional[uuid.UUID] = None) -> Tuple[Trip, List[DomainEvent]]:
        validate_state_transition(trip.status, TripStatus.IN_PROGRESS)
        
        now = datetime.now(timezone.utc)
        updated = trip.model_copy(update={
            "status": TripStatus.IN_PROGRESS,
            "started_at": now,
            "origin": origin,
            "driver_assignment_id": driver_assignment_id
        })
        
        event = TripStarted(
            trip_id=updated.trip_id,
            started_at=now,
            origin_latitude=origin.latitude,
            origin_longitude=origin.longitude
        )
        return updated, [event]

    @classmethod
    def pause_trip(cls, trip: Trip) -> Tuple[Trip, List[DomainEvent]]:
        validate_state_transition(trip.status, TripStatus.PAUSED)
        
        updated = trip.model_copy(update={"status": TripStatus.PAUSED})
        event = TripPaused(trip_id=updated.trip_id)
        return updated, [event]

    @classmethod
    def resume_trip(cls, trip: Trip) -> Tuple[Trip, List[DomainEvent]]:
        validate_state_transition(trip.status, TripStatus.IN_PROGRESS)
        
        updated = trip.model_copy(update={"status": TripStatus.IN_PROGRESS})
        event = TripResumed(trip_id=updated.trip_id)
        return updated, [event]

    @classmethod
    def complete_trip(cls, trip: Trip, destination: Location) -> Tuple[Trip, List[DomainEvent]]:
        validate_state_transition(trip.status, TripStatus.COMPLETED)
        
        now = datetime.now(timezone.utc)
        updated = trip.model_copy(update={
            "status": TripStatus.COMPLETED,
            "ended_at": now,
            "destination": destination
        })
        
        event = TripCompleted(
            trip_id=updated.trip_id,
            ended_at=now,
            destination_latitude=destination.latitude,
            destination_longitude=destination.longitude,
            total_distance_km=updated.total_distance.value_km
        )
        return updated, [event]
        
    @classmethod
    def cancel_trip(cls, trip: Trip, reason: Optional[str] = None) -> Tuple[Trip, List[DomainEvent]]:
        validate_state_transition(trip.status, TripStatus.CANCELLED)
        
        updated = trip.model_copy(update={"status": TripStatus.CANCELLED})
        event = TripCancelled(trip_id=updated.trip_id, reason=reason)
        return updated, [event]
