"""
Trip Management Domain - Read-Only API
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from domain.trip.schemas import TripResponse, TripSummaryResponse
from domain.trip.service import TripService
from domain.trip.queries import TripQueryService
from domain.trip.repository import InMemoryTripRepository
from domain.trip.errors import TripNotFound

# The API only exposes GET endpoints since the Trip lifecycle is driven by the Operational Event Processor.

router = APIRouter(prefix="/trips", tags=["trips"])

# Dependency setup (in reality, provided by a DI container)
_repository = InMemoryTripRepository()
_service = TripService(_repository)
_queries = TripQueryService(_repository)

def get_trip_service() -> TripService:
    return _service

def get_trip_queries() -> TripQueryService:
    return _queries


@router.get("", response_model=List[TripSummaryResponse])
def list_trips(queries: TripQueryService = Depends(get_trip_queries)):
    # Simple unpaginated wrapper for testing
    summaries = queries.completed_trips() + queries.active_trips()
    return summaries


@router.get("/active", response_model=List[TripSummaryResponse])
def active_trips(queries: TripQueryService = Depends(get_trip_queries)):
    return queries.active_trips()


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: uuid.UUID,
    service: TripService = Depends(get_trip_service)
):
    try:
        trip = service.get_trip(trip_id)
        
        origin_schema = None
        if trip.origin:
            origin_schema = {"latitude": trip.origin.latitude, "longitude": trip.origin.longitude, "address": trip.origin.address}
            
        dest_schema = None
        if trip.destination:
            dest_schema = {"latitude": trip.destination.latitude, "longitude": trip.destination.longitude, "address": trip.destination.address}
        
        return TripResponse(
            trip_id=trip.trip_id,
            organization_id=trip.organization_id,
            vehicle_id=trip.vehicle_id,
            driver_assignment_id=trip.driver_assignment_id,
            status=trip.status,
            started_at=trip.started_at,
            ended_at=trip.ended_at,
            origin=origin_schema,
            destination=dest_schema,
            total_distance_km=trip.total_distance.value_km,
            driving_duration_seconds=trip.driving_duration.value_seconds,
            idle_duration_seconds=trip.idle_duration.value_seconds,
            stop_count=trip.stop_count,
            metadata=trip.metadata
        )
    except TripNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
