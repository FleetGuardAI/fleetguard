"""
Trip Management Domain - Query Layer
"""

import uuid
from typing import List, Optional
from datetime import datetime

from domain.trip.repository import BaseTripRepository
from domain.trip.models import TripStatus
from domain.trip.projections import (
    TripSummary,
    ActiveTripSummary,
    VehicleTripSummary,
    DriverTripSummary
)

class TripQueryService:
    """
    Provides optimized read models for the Trip domain.
    """
    def __init__(self, repository: BaseTripRepository):
        self._repository = repository

    def active_trips(self) -> List[ActiveTripSummary]:
        trips = self._repository.list()
        return [
            ActiveTripSummary(
                trip_id=t.trip_id,
                vehicle_id=t.vehicle_id,
                status=t.status,
                started_at=t.started_at,
                total_distance_km=t.total_distance.value_km
            ) for t in trips if t.status == TripStatus.IN_PROGRESS
        ]

    def completed_trips(self) -> List[TripSummary]:
        trips = self._repository.list()
        return [
            TripSummary(
                trip_id=t.trip_id,
                vehicle_id=t.vehicle_id,
                status=t.status,
                started_at=t.started_at,
                total_distance_km=t.total_distance.value_km
            ) for t in trips if t.status == TripStatus.COMPLETED
        ]

    def trips_by_vehicle(self, vehicle_id: str) -> List[VehicleTripSummary]:
        trips = self._repository.list()
        return [
            VehicleTripSummary(
                trip_id=t.trip_id,
                vehicle_id=t.vehicle_id,
                status=t.status,
                started_at=t.started_at,
                total_distance_km=t.total_distance.value_km
            ) for t in trips if t.vehicle_id == vehicle_id
        ]

    def trips_by_driver(self, driver_assignment_id: uuid.UUID) -> List[DriverTripSummary]:
        trips = self._repository.list()
        return [
            DriverTripSummary(
                trip_id=t.trip_id,
                vehicle_id=t.vehicle_id,
                status=t.status,
                started_at=t.started_at,
                total_distance_km=t.total_distance.value_km,
                driver_assignment_id=t.driver_assignment_id
            ) for t in trips if t.driver_assignment_id == driver_assignment_id
        ]

    def trips_by_date(self, date: datetime) -> List[TripSummary]:
        trips = self._repository.list()
        # simplified date match for demonstration
        date_str = date.date().isoformat()
        return [
            TripSummary(
                trip_id=t.trip_id,
                vehicle_id=t.vehicle_id,
                status=t.status,
                started_at=t.started_at,
                total_distance_km=t.total_distance.value_km
            ) for t in trips if t.started_at and t.started_at.date().isoformat() == date_str
        ]
