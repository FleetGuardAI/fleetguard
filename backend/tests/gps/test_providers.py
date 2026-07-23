import unittest
from infrastructure.gps.providers.generic import GenericGPSProvider
from infrastructure.gps.providers.teltonika import TeltonikaProvider
from infrastructure.gps.models import GPSPosition

class TestGPSProviders(unittest.TestCase):
    def test_generic_provider(self):
        provider = GenericGPSProvider()
        payload = {
            "device_id": "dev123",
            "latitude": 12.0,
            "longitude": 77.0,
            "timestamp": "2023-01-01T00:00:00Z",
            "speed": 60,
            "heading": 90,
            "ignition": 1
        }
        pos = provider.receive(payload)
        self.assertIsInstance(pos, GPSPosition)
        self.assertEqual(pos.device_id, "dev123")
        self.assertEqual(pos.speed, 60.0)
        self.assertTrue(pos.ignition)

    def test_teltonika_provider(self):
        provider = TeltonikaProvider()
        payload = {
            "imei": "1234567890",
            "latitude": 12.0,
            "longitude": 77.0,
            "timestamp": "2023-01-01T00:00:00Z"
        }
        pos = provider.receive(payload)
        self.assertEqual(pos.device_id, "1234567890")
        self.assertEqual(pos.provider, "teltonika")
