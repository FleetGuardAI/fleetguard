"""
Trip Management Domain - Repository
"""

import abc
import uuid
from typing import List, Optional
from domain.trip.models import Trip, TripStatus

class BaseTripRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, trip: Trip) -> None:
        pass
        
    @abc.abstractmethod
    def update(self, trip: Trip) -> None:
        pass
        
    @abc.abstractmethod
    def find_by_id(self, trip_id: uuid.UUID) -> Optional[Trip]:
        pass

    @abc.abstractmethod
    def find_active_trip_for_vehicle(self, vehicle_id: str) -> Optional[Trip]:
        pass

    @abc.abstractmethod
    def list(self) -> List[Trip]:
        pass

class InMemoryTripRepository(BaseTripRepository):
    def __init__(self):
        self._trips = {}

    def create(self, trip: Trip) -> None:
        self._trips[trip.trip_id] = trip
        
    def update(self, trip: Trip) -> None:
        self._trips[trip.trip_id] = trip
        
    def find_by_id(self, trip_id: uuid.UUID) -> Optional[Trip]:
        return self._trips.get(trip_id)

    def find_active_trip_for_vehicle(self, vehicle_id: str) -> Optional[Trip]:
        for trip in self._trips.values():
            if trip.vehicle_id == vehicle_id and trip.status in (TripStatus.CREATED, TripStatus.IN_PROGRESS, TripStatus.PAUSED):
                return trip
        return None

    def list(self) -> List[Trip]:
        return list(self._trips.values())
