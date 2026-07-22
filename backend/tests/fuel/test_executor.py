import unittest
from infrastructure.fuel.executor import FuelGatewayExecutor
from infrastructure.fuel.registry import FuelProviderRegistry
from infrastructure.fuel.providers.generic import GenericFuelProvider
from infrastructure.fuel.models import FuelProcessingStatus

class TestFuelExecutor(unittest.TestCase):
    def setUp(self):
        self.registry = FuelProviderRegistry()
        self.registry.register(GenericFuelProvider)
        self.executor = FuelGatewayExecutor(self.registry)

    def test_process_payload_provider_not_found(self):
        result = self.executor.process_payload("unknown_key", {})
        self.assertEqual(result.processing_status, FuelProcessingStatus.UNKNOWN_PROVIDER)

    def test_process_payload_validation_failed(self):
        result = self.executor.process_payload("generic", {"device_id": "1"}) # Missing fields
        self.assertEqual(result.processing_status, FuelProcessingStatus.VALIDATION_ERROR)
        
    def test_process_payload_success(self):
        payload = {
            "device_id": "dev123",
            "timestamp": "2023-01-01T00:00:00Z",
            "fuel_level": "100.5",
            "unit": "L",
            "status": "OK"
        }
        result = self.executor.process_payload("generic", payload)
        self.assertEqual(result.processing_status, FuelProcessingStatus.SUCCESS)
        self.assertIsNotNone(result.telemetry)
        self.assertEqual(len(result.operational_events), 2) # FuelLevelRecorded and SensorStatusChanged
