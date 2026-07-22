import unittest
from infrastructure.fuel.providers.omnicomm import OmnicommProvider
from infrastructure.fuel.models import FuelTelemetry, MeasurementUnit

class TestFuelProviders(unittest.TestCase):
    def test_omnicomm_provider(self):
        provider = OmnicommProvider()
        payload = {
            "sensor_id": "omni_1",
            "time": "2023-01-01T00:00:00Z",
            "level": "4095",
            "temp": "25"
        }
        tel = provider.receive(payload)
        self.assertIsInstance(tel, FuelTelemetry)
        self.assertEqual(tel.device_id, "omni_1")
        self.assertEqual(tel.fuel_level, 4095.0)
        self.assertEqual(tel.measurement_unit, MeasurementUnit.ADC)
        self.assertEqual(tel.temperature, 25.0)
