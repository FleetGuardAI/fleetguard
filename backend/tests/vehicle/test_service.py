import unittest
import uuid
from domain.vehicle.schemas import RegisterVehicleRequest
from domain.vehicle.models import VehicleCategory, FuelType, OwnershipType
from domain.vehicle.repository import InMemoryVehicleRepository
from domain.vehicle.vehicle_service import VehicleService
from domain.vehicle.errors import DuplicateRegistration

class TestVehicleService(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryVehicleRepository()
        self.service = VehicleService(self.repo)
        
    def test_register_duplicate(self):
        req = RegisterVehicleRequest(
            registration_number="DUP-1",
            organization_id=uuid.uuid4(),
            make="Make",
            model="Model",
            manufacturing_year=2020,
            category=VehicleCategory.TRUCK,
            fuel_type=FuelType.DIESEL,
            ownership_type=OwnershipType.OWNED
        )
        
        self.service.register_vehicle(req)
        
        with self.assertRaises(DuplicateRegistration):
            self.service.register_vehicle(req)
