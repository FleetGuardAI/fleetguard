import unittest
from domain.device_registry.registry import DeviceRegistry
from domain.device_registry.models import Device, DeviceType

class TestDeviceRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = DeviceRegistry()

    def test_register_and_get(self):
        dev = Device(provider="omnicomm", serial_number="sn-1", device_type=DeviceType.FUEL_SENSOR)
        self.registry.register_device(dev)
        
        found = self.registry.get_device("omnicomm", "sn-1")
        self.assertIsNotNone(found)
        self.assertEqual(found.device_id, dev.device_id)
        
    def test_duplicate_registration(self):
        dev = Device(provider="omnicomm", serial_number="sn-1", device_type=DeviceType.FUEL_SENSOR)
        self.registry.register_device(dev)
        with self.assertRaises(ValueError):
            self.registry.register_device(dev)

    def test_update_metadata(self):
        dev = Device(provider="omnicomm", serial_number="sn-1", device_type=DeviceType.FUEL_SENSOR, metadata={"fw": "v1"})
        self.registry.register_device(dev)
        
        updated = self.registry.update_metadata("omnicomm", "sn-1", {"fw": "v2", "last_ping": "now"})
        self.assertEqual(updated.metadata["fw"], "v2")
        self.assertEqual(updated.metadata["last_ping"], "now")
        
        # Verify the list contains the updated one
        found = self.registry.get_device("omnicomm", "sn-1")
        self.assertEqual(found.metadata["fw"], "v2")
