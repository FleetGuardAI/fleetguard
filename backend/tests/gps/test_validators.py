import unittest
from infrastructure.gps.validators import validate_telemetry_payload

class TestGPSValidators(unittest.TestCase):
    def test_missing_fields(self):
        payload = {"lat": 1.0}
        with self.assertRaises(ValueError):
            validate_telemetry_payload(payload, ["device_id", "lat"])
            
    def test_latitude_bounds(self):
        with self.assertRaises(ValueError):
            validate_telemetry_payload({"latitude": 100.0}, [])
        with self.assertRaises(ValueError):
            validate_telemetry_payload({"latitude": -100.0}, [])

    def test_longitude_bounds(self):
        with self.assertRaises(ValueError):
            validate_telemetry_payload({"longitude": 200.0}, [])
            
    def test_speed_bounds(self):
        with self.assertRaises(ValueError):
            validate_telemetry_payload({"speed": -10.0}, [])
        with self.assertRaises(ValueError):
            validate_telemetry_payload({"speed": 5000.0}, [])

    def test_valid_payload(self):
        # Should not raise exception
        validate_telemetry_payload({"latitude": 12.0, "longitude": 77.0, "speed": 60, "device": "123"}, ["device"])
