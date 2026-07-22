import unittest
from datetime import datetime, timezone
import uuid
from pydantic import ValidationError
from domain.device_registry.models import Device, DeviceType, DeviceStatus, EntityType, MappingStatus, DeviceMapping

class TestDeviceModels(unittest.TestCase):
    def test_device_immutability(self):
        dev = Device(
            provider="teltonika",
            serial_number="12345",
            device_type=DeviceType.GPS_TRACKER
        )
        with self.assertRaises(ValidationError):
            dev.status = DeviceStatus.ACTIVE
            
    def test_mapping_immutability(self):
        mapping = DeviceMapping(
            device_id=uuid.uuid4(),
            entity_type=EntityType.VEHICLE,
            entity_id="v1"
        )
        with self.assertRaises(ValidationError):
            mapping.status = MappingStatus.INACTIVE
