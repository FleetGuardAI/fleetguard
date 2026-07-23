import unittest
from infrastructure.gps.executor import GPSGatewayExecutor
from infrastructure.gps.registry import GPSProviderRegistry
from infrastructure.gps.providers.generic import GenericGPSProvider
from infrastructure.gps.providers.teltonika import TeltonikaProvider
from infrastructure.gps.models import GPSProcessingStatus
from infrastructure.gps.events import PositionRecorded, IgnitionStateChanged

class TestGPSPipeline(unittest.TestCase):
    def setUp(self):
        self.registry = GPSProviderRegistry()
        self.registry.register(GenericGPSProvider)
        self.registry.register(TeltonikaProvider)
        self.executor = GPSGatewayExecutor(self.registry)

    def test_pipeline_teltonika_full(self):
        payload = {
            "imei": "999888777",
            "latitude": "12.345",
            "longitude": "77.654",
            "altitude": "100",
            "speed": "50", # Assuming km/h is generic speed unit here for testing
            "heading": "180",
            "ignition": 1,
            "timestamp": 1672531200
        }
        
        result = self.executor.process_payload("teltonika", payload)
        self.assertEqual(result.processing_status, GPSProcessingStatus.SUCCESS)
        
        pos = result.position
        self.assertEqual(pos.device_id, "999888777")
        self.assertEqual(pos.latitude, 12.345)
        self.assertEqual(pos.speed, 50.0)
        self.assertTrue(pos.ignition)
        
        # Operational events
        self.assertEqual(len(result.operational_events), 2)
        pos_event = next(e for e in result.operational_events if isinstance(e, PositionRecorded))
        ign_event = next(e for e in result.operational_events if isinstance(e, IgnitionStateChanged))
        
        self.assertEqual(pos_event.latitude, 12.345)
        self.assertTrue(ign_event.ignition_on)
