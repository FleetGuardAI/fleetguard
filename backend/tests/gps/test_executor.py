import unittest
from infrastructure.gps.executor import GPSGatewayExecutor
from infrastructure.gps.registry import GPSProviderRegistry
from infrastructure.gps.providers.generic import GenericGPSProvider
from infrastructure.gps.models import GPSProcessingStatus

class TestGPSExecutor(unittest.TestCase):
    def setUp(self):
        self.registry = GPSProviderRegistry()
        self.registry.register(GenericGPSProvider)
        self.executor = GPSGatewayExecutor(self.registry)

    def test_process_payload_provider_not_found(self):
        result = self.executor.process_payload("unknown_key", {})
        self.assertEqual(result.processing_status, GPSProcessingStatus.PROVIDER_NOT_FOUND)

    def test_process_payload_validation_failed(self):
        result = self.executor.process_payload("generic", {"lat": 12.0}) # Missing fields
        self.assertEqual(result.processing_status, GPSProcessingStatus.VALIDATION_FAILED)
        
    def test_process_payload_success(self):
        payload = {
            "device_id": "dev123",
            "latitude": 12.0,
            "longitude": 77.0,
            "timestamp": "2023-01-01T00:00:00Z",
            "speed": 60,
            "ignition": "on"
        }
        result = self.executor.process_payload("generic", payload)
        self.assertEqual(result.processing_status, GPSProcessingStatus.SUCCESS)
        self.assertIsNotNone(result.position)
        self.assertEqual(len(result.operational_events), 2) # PositionRecorded and IgnitionStateChanged
