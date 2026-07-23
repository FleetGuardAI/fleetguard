import unittest
import uuid
from domain.device_registry.models import Device, DeviceMapping, DeviceType, EntityType, MappingStatus
from domain.device_registry.validators import validate_duplicate_device, validate_mapping_conflict

class TestDeviceValidators(unittest.TestCase):
    def test_duplicate_device(self):
        dev1 = Device(provider="test", serial_number="123", device_type=DeviceType.GPS_TRACKER)
        existing = [dev1]
        
        with self.assertRaises(ValueError):
            validate_duplicate_device("test", "123", existing)
            
    def test_no_duplicate_device(self):
        dev1 = Device(provider="test", serial_number="123", device_type=DeviceType.GPS_TRACKER)
        existing = [dev1]
        # Should not raise
        validate_duplicate_device("test", "456", existing)

    def test_device_already_mapped(self):
        dev1 = Device(provider="test", serial_number="123", device_type=DeviceType.GPS_TRACKER)
        mapping = DeviceMapping(device_id=dev1.device_id, entity_type=EntityType.VEHICLE, entity_id="v1")
        
        with self.assertRaises(ValueError):
            validate_mapping_conflict(dev1, EntityType.VEHICLE, "v2", [mapping], [dev1])

    def test_entity_already_has_device_type(self):
        dev1 = Device(provider="test", serial_number="123", device_type=DeviceType.GPS_TRACKER)
        dev2 = Device(provider="test", serial_number="456", device_type=DeviceType.GPS_TRACKER)
        
        mapping = DeviceMapping(device_id=dev1.device_id, entity_type=EntityType.VEHICLE, entity_id="v1")
        
        with self.assertRaises(ValueError):
            validate_mapping_conflict(dev2, EntityType.VEHICLE, "v1", [mapping], [dev1, dev2])

    def test_entity_can_have_different_device_types(self):
        dev1 = Device(provider="test", serial_number="123", device_type=DeviceType.GPS_TRACKER)
        dev2 = Device(provider="test", serial_number="456", device_type=DeviceType.FUEL_SENSOR)
        
        mapping = DeviceMapping(device_id=dev1.device_id, entity_type=EntityType.VEHICLE, entity_id="v1")
        
        # Should not raise, fuel sensor is different than gps tracker
        validate_mapping_conflict(dev2, EntityType.VEHICLE, "v1", [mapping], [dev1, dev2])
