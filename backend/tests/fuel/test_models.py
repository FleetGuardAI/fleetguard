import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from infrastructure.fuel.models import FuelTelemetry, MeasurementUnit, TelemetryQuality, FuelProcessingResult, FuelProcessingStatus

class TestFuelModels(unittest.TestCase):
    def test_fuel_telemetry_immutability(self):
        tel = FuelTelemetry(
            provider="test",
            device_id="dev1",
            fuel_level=100.5,
            measurement_unit=MeasurementUnit.LITRES,
            timestamp=datetime.now(timezone.utc)
        )
        with self.assertRaises(ValidationError):
            tel.fuel_level = 90.0

    def test_processing_result_immutability(self):
        res = FuelProcessingResult(
            processing_status=FuelProcessingStatus.SUCCESS,
            execution_time_ms=10.0
        )
        with self.assertRaises(ValidationError):
            res.execution_time_ms = 20.0
