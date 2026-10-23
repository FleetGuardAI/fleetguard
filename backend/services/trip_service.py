"""
FleetGuard — Trip Service
Domain service orchestrating business rules for Trip Management.
"""

import uuid
from typing import Optional, Sequence, Set, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork
from datetime import datetime, timezone

from models.operational_event import OperationalEvent, EventType, EntityType, CaptureMethod, VerificationStatus
from models.trip_domain import Trip, TripStatus
from repositories.trip_repository import TripRepository


class TripDomainError(Exception):
    """Base exception for Trip domain errors."""
    pass


class TripNotFoundError(TripDomainError):
    pass


class InvalidTripStateTransitionError(TripDomainError):
    pass


class ResourceConflictError(TripDomainError):
    pass


class ResourceUnsuitableError(TripDomainError):
    pass


ALLOWED_TRANSITIONS: Dict[TripStatus, Set[TripStatus]] = {
    TripStatus.CREATED: {TripStatus.IN_PROGRESS, TripStatus.CANCELLED},
    TripStatus.IN_PROGRESS: {TripStatus.PAUSED, TripStatus.COMPLETED, TripStatus.CANCELLED},
    TripStatus.PAUSED: {TripStatus.IN_PROGRESS, TripStatus.COMPLETED, TripStatus.CANCELLED},
    TripStatus.COMPLETED: set(),
    TripStatus.CANCELLED: set(),
}


def validate_state_transition(current: TripStatus, target: TripStatus) -> bool:
    """Check whether a transition from current to target status is valid."""
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, set())


def create_trip_operational_event(
    company_id: int,
    event_type: EventType,
    trip_business_id: str,
    payload: Optional[dict] = None,
    created_by: Optional[str] = None
) -> OperationalEvent:
    """Construct an authoritative OperationalEvent instance for trip lifecycle transitions."""
    return OperationalEvent(
        id=uuid.uuid4(),
        company_id=company_id,
        event_type=event_type,
        entity_type=EntityType.TRIP,
        entity_id=trip_business_id,
        occurred_at=datetime.now(timezone.utc),
        capture_method=CaptureMethod.API_INTEGRATION,
        verification_status=VerificationStatus.VERIFIED,
        created_by=created_by,
        payload=payload or {}
    )


class TripService:
    """
    Coordinates Trip Domain business rules.
    Receives Canonical Events or handles read-only queries from the API.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for state mutation in the Trip Domain.
        Reads a verified OperationalEvent and applies business rules.
        """
        if event.entity_type != EntityType.TRIP:
            return  # The trip domain only cares about Trip entities

        payload = event.payload or {}
        
        # We assume entity_id maps to the external/business trip_id
        trip_business_id = event.entity_id

        # Route by event type
        if event.event_type == EventType.TRIP_CREATED:
            await self._record_trip_created(
                trip_business_id=trip_business_id,
                payload=payload,
                origin_id=str(event.id)
            )

        elif event.event_type == EventType.TRIP_STARTED:
            await self._record_trip_started(
                trip_business_id=trip_business_id,
                payload=payload,
                origin_id=str(event.id)
            )
            
        elif event.event_type == EventType.TRIP_PAUSED:
            await self._record_trip_paused(
                trip_business_id=trip_business_id,
                payload=payload,
                origin_id=str(event.id)
            )

        elif event.event_type == EventType.TRIP_RESUMED:
            await self._record_trip_resumed(
                trip_business_id=trip_business_id,
                payload=payload,
                origin_id=str(event.id)
            )

        elif event.event_type == EventType.TRIP_COMPLETED:
            await self._record_trip_completed(
                trip_business_id=trip_business_id,
                payload=payload,
                origin_id=str(event.id)
            )

        elif event.event_type == EventType.TRIP_CANCELLED:
            await self._record_trip_cancelled(
                trip_business_id=trip_business_id,
                payload=payload,
                origin_id=str(event.id)
            )

        elif event.event_type == EventType.TRIP_DRIVER_ASSIGNED:
            await self._record_trip_driver_assigned(
                trip_business_id=trip_business_id,
                payload=payload,
                origin_id=str(event.id)
            )

        elif event.event_type == EventType.TRIP_VEHICLE_ASSIGNED:
            await self._record_trip_vehicle_assigned(
                trip_business_id=trip_business_id,
                payload=payload,
                origin_id=str(event.id)
            )

    async def _record_trip_created(self, trip_business_id: str, payload: dict, origin_id: str) -> None:
        trip = await self.uow.repositories.trip.get_trip_by_business_id(trip_business_id)
        if not trip:
            trip = Trip(
                trip_id=trip_business_id,
                status=TripStatus.CREATED,
                origin_type="verified_event",
                origin_id=origin_id
            )
            
        trip.origin_location = payload.get("origin_location", trip.origin_location)
        trip.destination_location = payload.get("destination_location", trip.destination_location)
        trip.planned_distance = payload.get("planned_distance", trip.planned_distance)
        
        if "planned_start_time" in payload:
            try:
                trip.planned_start_time = datetime.fromisoformat(payload["planned_start_time"])
            except (ValueError, TypeError):
                pass
                
        if "planned_end_time" in payload:
            try:
                trip.planned_end_time = datetime.fromisoformat(payload["planned_end_time"])
            except (ValueError, TypeError):
                pass

        if "vehicle_id" in payload:
            trip.vehicle_id = payload["vehicle_id"]
        
        if "driver_id" in payload:
            trip.driver_id = payload["driver_id"]

        # Financial fields
        if "revenue" in payload:
            trip.revenue = payload["revenue"]
        if "planned_cost" in payload:
            trip.planned_cost = payload["planned_cost"]
        if "planned_fuel_liters" in payload:
            trip.planned_fuel_liters = payload["planned_fuel_liters"]
        if "cargo_weight" in payload:
            trip.cargo_weight = payload["cargo_weight"]

        await self.uow.repositories.trip.upsert_trip(trip)
        
    async def _record_trip_started(self, trip_business_id: str, payload: dict, origin_id: str) -> None:
        trip = await self.uow.repositories.trip.get_trip_by_business_id(trip_business_id)
        if not trip:
            return

        # Terminal state protection against replay or invalid transitions
        if trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
            return

        trip.status = TripStatus.IN_PROGRESS
        trip.origin_type = "verified_event"
        trip.origin_id = origin_id
        
        if "actual_start_time" in payload:
            try:
                trip.actual_start_time = datetime.fromisoformat(payload["actual_start_time"])
            except (ValueError, TypeError):
                pass
        
        await self.uow.repositories.trip.upsert_trip(trip)

    async def _record_trip_paused(self, trip_business_id: str, payload: dict, origin_id: str) -> None:
        trip = await self.uow.repositories.trip.get_trip_by_business_id(trip_business_id)
        if not trip or trip.status != TripStatus.IN_PROGRESS:
            return
            
        trip.status = TripStatus.PAUSED
        trip.origin_type = "verified_event"
        trip.origin_id = origin_id
        await self.uow.repositories.trip.upsert_trip(trip)

    async def _record_trip_resumed(self, trip_business_id: str, payload: dict, origin_id: str) -> None:
        trip = await self.uow.repositories.trip.get_trip_by_business_id(trip_business_id)
        if not trip or trip.status != TripStatus.PAUSED:
            return

        trip.status = TripStatus.IN_PROGRESS
        trip.origin_type = "verified_event"
        trip.origin_id = origin_id
        await self.uow.repositories.trip.upsert_trip(trip)
        
    async def _record_trip_completed(self, trip_business_id: str, payload: dict, origin_id: str) -> None:
        trip = await self.uow.repositories.trip.get_trip_by_business_id(trip_business_id)
        if not trip:
            return

        # Terminal state protection
        if trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
            return

        trip.status = TripStatus.COMPLETED
        trip.origin_type = "verified_event"
        trip.origin_id = origin_id
        
        if "actual_end_time" in payload:
            try:
                trip.actual_end_time = datetime.fromisoformat(payload["actual_end_time"])
            except (ValueError, TypeError):
                pass
                
        if "actual_distance" in payload:
            trip.actual_distance = payload["actual_distance"]
            
        await self.uow.repositories.trip.upsert_trip(trip)
        
    async def _record_trip_cancelled(self, trip_business_id: str, payload: dict, origin_id: str) -> None:
        trip = await self.uow.repositories.trip.get_trip_by_business_id(trip_business_id)
        if not trip:
            return

        # Cannot cancel a completed trip
        if trip.status == TripStatus.COMPLETED:
            return

        trip.status = TripStatus.CANCELLED
        trip.origin_type = "verified_event"
        trip.origin_id = origin_id
        await self.uow.repositories.trip.upsert_trip(trip)

    async def _record_trip_driver_assigned(self, trip_business_id: str, payload: dict, origin_id: str) -> None:
        trip = await self.uow.repositories.trip.get_trip_by_business_id(trip_business_id)
        if not trip or trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
            return
            
        if "driver_id" in payload:
            trip.driver_id = payload["driver_id"]
            trip.origin_type = "verified_event"
            trip.origin_id = origin_id
            await self.uow.repositories.trip.upsert_trip(trip)

    async def _record_trip_vehicle_assigned(self, trip_business_id: str, payload: dict, origin_id: str) -> None:
        trip = await self.uow.repositories.trip.get_trip_by_business_id(trip_business_id)
        if not trip or trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
            return
            
        if "vehicle_id" in payload:
            trip.vehicle_id = payload["vehicle_id"]
            trip.origin_type = "verified_event"
            trip.origin_id = origin_id
            await self.uow.repositories.trip.upsert_trip(trip)

    # --- Read APIs ---

    async def get_trip(self, trip_id: int, company_id: Optional[int] = None) -> Optional[Trip]:
        return await self.uow.repositories.trip.get_trip_by_id(trip_id, company_id=company_id)
        
    async def get_trips_by_vehicle(
        self, vehicle_id: int, limit: int = 50, offset: int = 0, company_id: Optional[int] = None
    ) -> Sequence[Trip]:
        return await self.uow.repositories.trip.get_trips_by_vehicle(vehicle_id, limit=limit, offset=offset, company_id=company_id)

    async def get_trips_by_driver(
        self, driver_id: int, limit: int = 50, offset: int = 0, company_id: Optional[int] = None
    ) -> Sequence[Trip]:
        return await self.uow.repositories.trip.get_trips_by_driver(driver_id, limit=limit, offset=offset, company_id=company_id)

    async def search_trips(
        self, 
        status: Optional[TripStatus] = None, 
        limit: int = 50, 
        offset: int = 0,
        company_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> Sequence[Trip]:
        return await self.uow.repositories.trip.search_trips(
            status=status, 
            limit=limit, 
            offset=offset, 
            company_id=company_id,
            search=search
        )

