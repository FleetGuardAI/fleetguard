import time
import unittest

from infrastructure.intelligence.event_processing.models import GPSEvent, FuelReceiptEvent
from infrastructure.intelligence.event_processing.correlator import EventCorrelator

class TestEventCorrelator(unittest.TestCase):
    def test_correlation_window(self):
        correlator = EventCorrelator(window_seconds=0.1)
        
        gps = GPSEvent(correlation_id="tx_1", latitude=0.0, longitude=0.0, accuracy=10.0)
        receipt = FuelReceiptEvent(correlation_id="tx_1", quantity=100.0, amount=100.0)
        
        correlator.add_event(gps)
        correlator.add_event(receipt)
        
        # Immediate check - window not expired
        txs = correlator.get_ready_transactions()
        self.assertEqual(len(txs), 0)
        
        # Wait for window to expire
        time.sleep(0.15)
        
        txs = correlator.get_ready_transactions()
        self.assertEqual(len(txs), 1)
        self.assertEqual(len(txs[0]), 2)
        self.assertIn(gps, txs[0])
        self.assertIn(receipt, txs[0])

    def test_multiple_correlation_ids(self):
        correlator = EventCorrelator(window_seconds=0.1)
        
        e1 = GPSEvent(correlation_id="tx_1", latitude=0.0, longitude=0.0, accuracy=10.0)
        e2 = GPSEvent(correlation_id="tx_2", latitude=1.0, longitude=1.0, accuracy=10.0)
        
        correlator.add_event(e1)
        time.sleep(0.05)
        correlator.add_event(e2)
        
        time.sleep(0.06)
        
        # Only tx_1 should be ready
        txs = correlator.get_ready_transactions()
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0][0].correlation_id, "tx_1")
        
        time.sleep(0.06)
        
        # Now tx_2 should be ready
        txs = correlator.get_ready_transactions()
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0][0].correlation_id, "tx_2")

    def test_duplicate_events(self):
        correlator = EventCorrelator(window_seconds=0.1)
        
        gps = GPSEvent(correlation_id="tx_1", latitude=0.0, longitude=0.0, accuracy=10.0)
        
        # Simulating duplicate receipt (in a real system, would be deduped by event_id, but here it just buffers)
        correlator.add_event(gps)
        correlator.add_event(gps)
        
        time.sleep(0.15)
        
        txs = correlator.get_ready_transactions()
        self.assertEqual(len(txs), 1)
        self.assertEqual(len(txs[0]), 2)
