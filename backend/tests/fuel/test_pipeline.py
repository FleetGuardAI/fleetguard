import unittest
from infrastructure.fuel.executor import FuelGatewayExecutor
from infrastructure.fuel.registry import FuelProviderRegistry
from infrastructure.fuel.providers.escort import EscortProvider
from infrastructure.fuel.models import FuelProcessingStatus
from infrastructure.fuel.events import FuelLevelRecorded

class TestFuelPipeline(unittest.TestCase):
    def setUp(self):
        self.registry = FuelProviderRegistry()
        self.registry.register(EscortProvider)
        self.executor = FuelGatewayExecutor(self.registry)

    def test_pipeline_escort_full(self):
        payload = {
            "id": "escort_sensor_1",
            "datetime": 1672531200,
            "level": "2048",
            "t": "30.5"
        }
        
        result = self.executor.process_payload("escort", payload)
        self.assertEqual(result.processing_status, FuelProcessingStatus.SUCCESS)
        
        tel = result.telemetry
        self.assertEqual(tel.device_id, "escort_sensor_1")
        self.assertEqual(tel.fuel_level, 2048.0)
        self.assertEqual(tel.temperature, 30.5)
        
        # Operational events
        self.assertEqual(len(result.operational_events), 1) # Only FuelLevelRecorded as no health status
        level_event = result.operational_events[0]
        self.assertIsInstance(level_event, FuelLevelRecorded)
        
        self.assertEqual(level_event.fuel_level, 2048.0)
        self.assertEqual(level_event.temperature, 30.5)
