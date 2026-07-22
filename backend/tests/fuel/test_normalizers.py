import unittest
from datetime import datetime, timezone
from infrastructure.fuel.models import MeasurementUnit, TelemetryQuality
from infrastructure.fuel.normalizers import (
    normalize_fuel_level,
    normalize_temperature,
    normalize_measurement_unit,
    normalize_quality,
    normalize_timestamp
)

class TestFuelNormalizers(unittest.TestCase):
    def test_normalize_fuel_level(self):
        self.assertEqual(normalize_fuel_level(12.3456789), 12.3457)

    def test_normalize_temperature(self):
        self.assertEqual(normalize_temperature(25.123), 25.12)

    def test_normalize_measurement_unit(self):
        self.assertEqual(normalize_measurement_unit("L"), MeasurementUnit.LITRES)
        self.assertEqual(normalize_measurement_unit("%"), MeasurementUnit.PERCENTAGE)
        self.assertEqual(normalize_measurement_unit("adc"), MeasurementUnit.ADC)
        self.assertEqual(normalize_measurement_unit("unknown_thing"), MeasurementUnit.UNKNOWN)

    def test_normalize_quality(self):
        self.assertEqual(normalize_quality("HIGH"), TelemetryQuality.HIGH)
        self.assertEqual(normalize_quality("poor"), TelemetryQuality.LOW)
        
    def test_normalize_timestamp(self):
        dt = normalize_timestamp("2023-01-01T00:00:00Z")
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.tzinfo, timezone.utc)
