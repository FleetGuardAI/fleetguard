import unittest
from domain.device_registry.registry import DeviceRegistry
from domain.device_registry.mapping_service import DeviceMappingService
from domain.device_registry.models import Device, DeviceType, EntityType, MappingStatus

class TestDeviceMappingService(unittest.TestCase):
    def setUp(self):
        self.registry = DeviceRegistry()
        self.service = DeviceMappingService(self.registry)
        
        self.dev = Device(provider="teltonika", serial_number="123", device_type=DeviceType.GPS_TRACKER)
        self.registry.register_device(self.dev)

    def test_assign_device(self):
        mapping = self.service.assign_device(self.dev, EntityType.VEHICLE, "v-001")
        self.assertIsNotNone(mapping)
        self.assertEqual(mapping.status, MappingStatus.ACTIVE)
        
    def test_resolve_mapping(self):
        self.service.assign_device(self.dev, EntityType.VEHICLE, "v-001")
        mapping = self.service.resolve_mapping(self.dev.device_id)
        self.assertIsNotNone(mapping)
        self.assertEqual(mapping.entity_id, "v-001")
        
    def test_unassign_device(self):
        self.service.assign_device(self.dev, EntityType.VEHICLE, "v-001")
        unassigned = self.service.unassign_device(self.dev.device_id)
        
        self.assertEqual(unassigned.status, MappingStatus.INACTIVE)
        self.assertIsNotNone(unassigned.unassigned_at)
        
        mapping = self.service.resolve_mapping(self.dev.device_id)
        self.assertIsNone(mapping) # No active mapping anymore

    def test_reassign_device(self):
        # Assign to v-001
        self.service.assign_device(self.dev, EntityType.VEHICLE, "v-001")
        
        # Unassign
        self.service.unassign_device(self.dev.device_id)
        
        # Assign to v-002
        new_mapping = self.service.assign_device(self.dev, EntityType.VEHICLE, "v-002")
        self.assertEqual(new_mapping.entity_id, "v-002")
