import unittest
from infrastructure.fuel.validators import validate_telemetry_payload

class TestFuelValidators(unittest.TestCase):
    def test_missing_fields(self):
        payload = {"device_id": "1"}
        with self.assertRaises(ValueError):
            validate_telemetry_payload(payload, ["device_id", "fuel_level"])
            
    def test_invalid_fuel_level_type(self):
        with self.assertRaises(ValueError):
            validate_telemetry_payload({"fuel_level": "not_a_number"}, [])

    def test_valid_payload(self):
        validate_telemetry_payload({"device_id": "123", "fuel_level": "100.5"}, ["device_id"])
