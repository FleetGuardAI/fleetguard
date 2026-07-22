import unittest
import uuid
from domain.vehicle.api import VehicleAPI
from domain.vehicle.schemas import RegisterVehicleRequest, StateChangeRequest, UpdateConfigurationRequest
from domain.vehicle.models import VehicleCategory, FuelType, OwnershipType, VehicleStatus, VehicleConfiguration
from domain.vehicle.repository import InMemoryVehicleRepository
from domain.vehicle.vehicle_service import VehicleService
from domain.vehicle.queries import VehicleQueries

class TestVehiclePipeline(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryVehicleRepository()
        self.service = VehicleService(self.repo)
        self.queries = VehicleQueries(self.repo)
        self.api = VehicleAPI(self.service, self.queries)
        
    def test_end_to_end_lifecycle(self):
        org_id = uuid.uuid4()
        
        # 1. Register
        req = RegisterVehicleRequest(
            registration_number="TRK-999",
            organization_id=org_id,
            make="Volvo",
            model="FH16",
            manufacturing_year=2023,
            category=VehicleCategory.TRUCK,
            fuel_type=FuelType.DIESEL,
            ownership_type=OwnershipType.LEASED
        )
        resp1 = self.api.register_vehicle(req)
        self.assertEqual(resp1.status, VehicleStatus.INACTIVE)
        
        # 2. Activate
        resp2 = self.api.activate_vehicle(resp1.vehicle_id, StateChangeRequest(reason="Ready"))
        self.assertEqual(resp2.status, VehicleStatus.ACTIVE)
        
        # 3. Search
        active = self.api.list_organization_vehicles(org_id)
        self.assertEqual(len(active), 1)
        
        # 4. Update configuration
        new_config = VehicleConfiguration(average_expected_mileage=5.5)
        self.api.update_configuration(resp1.vehicle_id, UpdateConfigurationRequest(configuration=new_config))
        
        updated_vehicle = self.service.get_vehicle(resp1.vehicle_id)
        self.assertEqual(updated_vehicle.configuration.average_expected_mileage, 5.5)
