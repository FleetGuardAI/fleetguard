import unittest
import uuid
from domain.vehicle.models import Vehicle, VehicleCategory, FuelType, OwnershipType, VehicleStatus
from domain.vehicle.value_objects import RegistrationNumber
from domain.vehicle.aggregate import VehicleAggregate
from domain.vehicle.errors import InvalidVehicleState
from domain.vehicle.events import VehicleRegistered

class TestVehicleAggregate(unittest.TestCase):
    def setUp(self):
        self.vehicle = Vehicle(
            registration_number=RegistrationNumber(value="TEST-1"),
            make="Test",
            model="Model",
            manufacturing_year=2020,
            category=VehicleCategory.TRUCK,
            fuel_type=FuelType.DIESEL,
            ownership_type=OwnershipType.OWNED,
            organization_id=uuid.uuid4()
        )
        
    def test_register_vehicle(self):
        registered, events = VehicleAggregate.register_vehicle(self.vehicle)
        self.assertEqual(registered.status, VehicleStatus.INACTIVE)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], VehicleRegistered)
        
    def test_activate_vehicle(self):
        active, events = VehicleAggregate.activate_vehicle(self.vehicle)
        self.assertEqual(active.status, VehicleStatus.ACTIVE)
        self.assertEqual(len(events), 1)
        
    def test_archive_vehicle(self):
        archived, events = VehicleAggregate.archive_vehicle(self.vehicle)
        self.assertEqual(archived.status, VehicleStatus.ARCHIVED)
        
        with self.assertRaises(InvalidVehicleState):
            VehicleAggregate.activate_vehicle(archived)
