import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from infrastructure.gps.models import GPSPosition, ProviderCapabilities, GPSProcessingResult, GPSProcessingStatus

class TestGPSModels(unittest.TestCase):
    def test_gps_position_immutability(self):
        pos = GPSPosition(
            provider="test",
            device_id="dev1",
            latitude=12.34,
            longitude=56.78,
            timestamp=datetime.now(timezone.utc)
        )
        with self.assertRaises(ValidationError):
            pos.latitude = 90.0

    def test_provider_capabilities_immutability(self):
        cap = ProviderCapabilities(supports_ignition=True)
        with self.assertRaises(ValidationError):
            cap.supports_ignition = False

    def test_processing_result_immutability(self):
        res = GPSProcessingResult(
            processing_status=GPSProcessingStatus.SUCCESS,
            execution_time_ms=10.0
        )
        with self.assertRaises(ValidationError):
            res.execution_time_ms = 20.0
