import unittest

from infrastructure.intelligence.event_processing.models import GPSEvent, FuelReceiptEvent
from infrastructure.intelligence.event_processing.builder import EvidenceBuilder
from infrastructure.intelligence.evidence.models import ReceiptEvidence, GPSEvidence


class TestEvidenceBuilder(unittest.TestCase):
    def test_build_package_preserves_provenance(self):
        builder = EvidenceBuilder()
        
        gps = GPSEvent(correlation_id="tx_1", latitude=10.0, longitude=20.0, accuracy=5.0)
        receipt = FuelReceiptEvent(
            correlation_id="tx_1", quantity=100.0, amount=150.0,
            station_name="Test Station", station_lat=10.1, station_lon=20.1
        )
        
        package = builder.build_package([gps, receipt])
        
        self.assertTrue(package.has_evidence(GPSEvidence))
        self.assertTrue(package.has_evidence(ReceiptEvidence))
        
        gps_evidence = package.get_evidence(GPSEvidence)
        receipt_evidence = package.get_evidence(ReceiptEvidence)
        
        # Verify provenance
        self.assertEqual(gps_evidence.evidence_id, gps.event_id)
        self.assertEqual(receipt_evidence.evidence_id, receipt.event_id)
        
        self.assertEqual(gps_evidence.collected_at, gps.timestamp)
        self.assertEqual(receipt_evidence.collected_at, receipt.timestamp)
        
        # Verify specific fields mapped correctly
        self.assertEqual(gps_evidence.latitude, 10.0)
        self.assertEqual(receipt_evidence.quantity, 100.0)
        self.assertEqual(receipt_evidence.metadata.get("station_name"), "Test Station")
