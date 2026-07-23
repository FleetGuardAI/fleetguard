import unittest
from domain.device_registry.registry import DeviceRegistry
from domain.device_registry.mapping_service import DeviceMappingService
from domain.device_registry.models import Device, DeviceType, EntityType, MappingStatus

class TestDevicePipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.registry = DeviceRegistry()
        self.service = DeviceMappingService(self.registry)

    def test_full_device_lifecycle(self):
        # 1. Register a GPS Tracker
        gps = Device(provider="teltonika", serial_number="sn-gps-001", device_type=DeviceType.GPS_TRACKER)
        self.registry.register_device(gps)
        
        # 2. Register a Fuel Sensor
        fuel = Device(provider="omnicomm", serial_number="sn-fuel-001", device_type=DeviceType.FUEL_SENSOR)
        self.registry.register_device(fuel)

        # 3. Assign both to the same vehicle (should succeed, different device types)
        self.service.assign_device(gps, EntityType.VEHICLE, "fleet-v1")
        self.service.assign_device(fuel, EntityType.VEHICLE, "fleet-v1")
        
        # 4. Resolve the active mappings
        gps_map = self.service.resolve_mapping(gps.device_id)
        fuel_map = self.service.resolve_mapping(fuel.device_id)
        
        self.assertEqual(gps_map.entity_id, "fleet-v1")
        self.assertEqual(fuel_map.entity_id, "fleet-v1")
        
        # 5. Try to assign a second GPS tracker to the same vehicle
        gps2 = Device(provider="ruptela", serial_number="sn-gps-002", device_type=DeviceType.GPS_TRACKER)
        self.registry.register_device(gps2)
        
        with self.assertRaises(ValueError):
            self.service.assign_device(gps2, EntityType.VEHICLE, "fleet-v1")
            
        # 6. Unassign the first GPS tracker
        self.service.unassign_device(gps.device_id)
        
        # 7. Now assignment of the second GPS tracker should succeed
        self.service.assign_device(gps2, EntityType.VEHICLE, "fleet-v1")
        
        # 8. Verify resolution
        gps_map_new = self.service.resolve_mapping(gps2.device_id)
        self.assertEqual(gps_map_new.entity_id, "fleet-v1")
        
        old_map = self.service.resolve_mapping(gps.device_id)
        self.assertIsNone(old_map)
