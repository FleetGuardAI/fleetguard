import time
import unittest
from unittest.mock import MagicMock

from infrastructure.intelligence.event_processing.models import GPSEvent, FuelReceiptEvent
from infrastructure.intelligence.event_processing.correlator import EventCorrelator
from infrastructure.intelligence.event_processing.builder import EvidenceBuilder
from infrastructure.intelligence.event_processing.processor import EventProcessor


class TestEventProcessor(unittest.TestCase):
    def test_end_to_end_event_processing(self):
        correlator = EventCorrelator(window_seconds=0.1)
        builder = EvidenceBuilder()
        orchestrator = MagicMock()
        orchestrator.execute.return_value = "MOCKED_RESULT"
        
        processor = EventProcessor(
            correlator=correlator,
            builder=builder,
            orchestrator=orchestrator
        )
        
        gps = GPSEvent(correlation_id="tx_1", latitude=10.0, longitude=20.0, accuracy=5.0)
        receipt = FuelReceiptEvent(correlation_id="tx_1", quantity=100.0, amount=150.0)
        
        # Ingest first event
        res1 = processor.process_event(gps)
        self.assertEqual(len(res1), 0) # window not closed
        
        # Ingest second event
        res2 = processor.process_event(receipt)
        self.assertEqual(len(res2), 0)
        
        # Wait for window
        time.sleep(0.15)
        
        # Process a dummy event to trigger evaluation
        dummy = GPSEvent(correlation_id="tx_2", latitude=0.0, longitude=0.0, accuracy=0.0)
        res3 = processor.process_event(dummy)
        
        # Should return the result for tx_1
        self.assertEqual(len(res3), 1)
        self.assertEqual(res3[0], "MOCKED_RESULT")
        
        # Ensure orchestrator was called with a package containing our two events
        orchestrator.execute.assert_called_once()
        package = orchestrator.execute.call_args[0][0]
        
        self.assertEqual(len(package.iterate_all()), 2)
