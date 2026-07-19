import unittest
import uuid
from datetime import datetime
from pydantic import ValidationError

from infrastructure.intelligence.evidence.models import (
    Reliability,
    BaseEvidence,
    ReceiptEvidence,
    GPSEvidence,
    FuelSensorEvidence,
    VehicleEvidence,
    DriverEvidence
)
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.evidence.registry import EvidenceRegistry


class TestEvidenceFramework(unittest.TestCase):
    
    def setUp(self):
        self.now = datetime.now()
        
    def _build_receipt(self) -> ReceiptEvidence:
        return ReceiptEvidence(
            source="ocr_service",
            origin="driver_whatsapp",
            collected_at=self.now,
            reliability=Reliability.MEDIUM,
            quantity=50.0,
            amount=5000.0,
            station_name="Test Station"
        )
        
    def _build_gps(self) -> GPSEvidence:
        return GPSEvidence(
            source="telematics_gateway",
            origin="vehicle_tracker_v1",
            collected_at=self.now,
            reliability=Reliability.HIGH,
            latitude=18.5204,
            longitude=73.8567,
            accuracy=5.0
        )

    def test_evidence_immutability(self):
        receipt = self._build_receipt()
        
        # Ensure we can read properties
        self.assertEqual(receipt.source, "ocr_service")
        self.assertEqual(receipt.quantity, 50.0)
        
        # Pydantic v2 frozen models raise ValidationError on assignment
        with self.assertRaises(ValidationError):
            receipt.quantity = 60.0
            
        with self.assertRaises(ValidationError):
            receipt.source = "new_source"

    def test_evidence_strong_typing(self):
        # Missing required field for GPS (latitude)
        with self.assertRaises(ValidationError):
            GPSEvidence(
                source="telematics_gateway",
                origin="vehicle_tracker_v1",
                collected_at=self.now,
                reliability=Reliability.HIGH,
                longitude=73.8567,
                accuracy=5.0
            )

    def test_evidence_package_retrieval_and_existence(self):
        receipt = self._build_receipt()
        gps = self._build_gps()
        
        package = EvidencePackage([receipt, gps])
        
        # Test has_evidence
        self.assertTrue(package.has_evidence(ReceiptEvidence))
        self.assertTrue(package.has_evidence(GPSEvidence))
        self.assertFalse(package.has_evidence(FuelSensorEvidence))
        
        # Test get_evidence
        retrieved_receipt = package.get_evidence(ReceiptEvidence)
        self.assertIsNotNone(retrieved_receipt)
        self.assertEqual(retrieved_receipt.quantity, 50.0)
        
        # Test missing evidence returns None without raising
        self.assertIsNone(package.get_evidence(FuelSensorEvidence))

    def test_evidence_package_immutability(self):
        receipt = self._build_receipt()
        package = EvidencePackage([receipt])
        
        with self.assertRaises(AttributeError):
            package.new_attr = "test"
            
        with self.assertRaises(AttributeError):
            package._evidence_map = {}

    def test_evidence_package_duplicate_rejection(self):
        receipt1 = self._build_receipt()
        # Same exact instance, meaning same evidence_id
        receipt2 = receipt1
        
        with self.assertRaises(ValueError) as context:
            EvidencePackage([receipt1, receipt2])
            
        self.assertIn("Duplicate evidence_id detected", str(context.exception))

    def test_evidence_package_multiple_same_type(self):
        receipt1 = self._build_receipt()
        receipt2 = self._build_receipt() # Different UUID by default
        
        # Modify the second one slightly for testing
        package = EvidencePackage([receipt1, receipt2])
        
        # Test has_evidence
        self.assertTrue(package.has_evidence(ReceiptEvidence))
        
        # Test get_evidence (primary)
        primary = package.get_evidence(ReceiptEvidence)
        self.assertIsNotNone(primary)
        self.assertEqual(primary.evidence_id, receipt1.evidence_id)
        
        # Test get_all_evidence
        all_receipts = package.get_all_evidence(ReceiptEvidence)
        self.assertEqual(len(all_receipts), 2)
        self.assertIn(receipt1, all_receipts)
        self.assertIn(receipt2, all_receipts)

    def test_evidence_package_available_types_and_iteration(self):
        receipt1 = self._build_receipt()
        receipt2 = self._build_receipt()
        gps = self._build_gps()
        package = EvidencePackage([receipt1, receipt2, gps])
        
        types = package.available_types()
        self.assertEqual(len(types), 2)
        self.assertIn(ReceiptEvidence, types)
        self.assertIn(GPSEvidence, types)
        
        all_ev = package.iterate_all()
        self.assertEqual(len(all_ev), 3)

    def test_evidence_registry(self):
        registry = EvidenceRegistry()
        
        # Register a type
        registry.register(ReceiptEvidence)
        registry.register(GPSEvidence)
        
        # Enumerate
        registered = registry.enumerate_registered()
        self.assertIn("ReceiptEvidence", registered)
        self.assertIn("GPSEvidence", registered)
        
        # Lookup
        cls = registry.get_class("ReceiptEvidence")
        self.assertEqual(cls, ReceiptEvidence)
        
        # Duplicate registration
        with self.assertRaises(ValueError):
            registry.register(ReceiptEvidence)
            
        # Lookup unknown
        with self.assertRaises(ValueError):
            registry.get_class("UnknownEvidence")
