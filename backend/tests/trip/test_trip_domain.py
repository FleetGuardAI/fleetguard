import unittest
import uuid
import asyncio
from datetime import datetime, timezone

from domain.trip.models import Trip, TripStatus
from domain.trip.value_objects import Location
from domain.trip.service import TripService
from domain.trip.repository import InMemoryTripRepository
from domain.trip.event_handler import TripEventHandler
from domain.trip.errors import InvalidTripState, ImmutableTripError

class MockOperationalEvent:
    def __init__(self, event_type, entity_id, payload=None):
        class EventTypeObj:
            def __init__(self, val):
                self.value = val
        self.event_type = EventTypeObj(event_type)
        self.entity_id = entity_id
        self.payload = payload or {}

class TestTripDomain(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryTripRepository()
        self.service = TripService(self.repo)
        self.handler = TripEventHandler(self.service)
        self.org_id = uuid.uuid4()
        self.vehicle_id = "veh-123"

    def test_trip_lifecycle_via_events(self):
        # 1. Start Trip
        start_payload = {
            "organization_id": str(self.org_id),
            "location": {"latitude": 40.7128, "longitude": -74.0060},
            "driver_assignment_id": str(uuid.uuid4())
        }
        start_event = MockOperationalEvent("IGNITION_STARTED", self.vehicle_id, start_payload)
        
        asyncio.run(self.handler.handle_event(start_event))
        
        active_trip = self.repo.find_active_trip_for_vehicle(self.vehicle_id)
        self.assertIsNotNone(active_trip)
        self.assertEqual(active_trip.status, TripStatus.IN_PROGRESS)
        self.assertEqual(active_trip.origin.latitude, 40.7128)
        
        # 2. Complete Trip
        stop_payload = {
            "location": {"latitude": 42.3601, "longitude": -71.0589}
        }
        stop_event = MockOperationalEvent("IGNITION_STOPPED", self.vehicle_id, stop_payload)
        
        asyncio.run(self.handler.handle_event(stop_event))
        
        active_trip_after = self.repo.find_active_trip_for_vehicle(self.vehicle_id)
        self.assertIsNone(active_trip_after) # No active trips anymore
        
        completed_trip = self.repo.find_by_id(active_trip.trip_id)
        self.assertEqual(completed_trip.status, TripStatus.COMPLETED)
        self.assertEqual(completed_trip.destination.latitude, 42.3601)

    def test_immutable_completed_trip(self):
        start_payload = {
            "organization_id": str(self.org_id),
            "location": {"latitude": 1.0, "longitude": 1.0}
        }
        asyncio.run(self.handler.handle_event(MockOperationalEvent("IGNITION_STARTED", self.vehicle_id, start_payload)))
        asyncio.run(self.handler.handle_event(MockOperationalEvent("IGNITION_STOPPED", self.vehicle_id, {})))
        
        trip = self.repo.list()[0]
        self.assertEqual(trip.status, TripStatus.COMPLETED)
        
        from domain.trip.aggregate import TripAggregate
        with self.assertRaises(ImmutableTripError):
            TripAggregate.pause_trip(trip)

if __name__ == "__main__":
    unittest.main()
