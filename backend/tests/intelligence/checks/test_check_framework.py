import unittest
from typing import List, Type
import uuid
from datetime import datetime

from infrastructure.intelligence.evidence.models import BaseEvidence, Reliability
from infrastructure.intelligence.evidence.package import EvidencePackage

from infrastructure.intelligence.checks.models import CheckStatus, CheckResult
from infrastructure.intelligence.checks.base import BaseCheck
from infrastructure.intelligence.checks.registry import CheckRegistry
from infrastructure.intelligence.checks.executor import CheckExecutor

# Dummy Evidence for Testing
class TestReceiptEvidence(BaseEvidence):
    evidence_type: str = "TestReceiptEvidence"
    amount: float = 0.0

class TestGPSEvidence(BaseEvidence):
    evidence_type: str = "TestGPSEvidence"
    lat: float = 0.0
    lon: float = 0.0

# Dummy Checks for Testing
class ValidCheck(BaseCheck):
    @classmethod
    def key(cls) -> str:
        return "test.valid_check"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return [TestReceiptEvidence]
        
    @classmethod
    def optional_evidence(cls) -> List[Type[BaseEvidence]]:
        return [TestGPSEvidence]

    def execute(self, package: EvidencePackage) -> CheckResult:
        receipt = package.get_evidence(TestReceiptEvidence)
        gps = package.get_evidence(TestGPSEvidence)
        
        used = ["TestReceiptEvidence"]
        if gps:
            used.append("TestGPSEvidence")
            
        return CheckResult(
            check_key=self.key(),
            check_name=self.name(),
            status=CheckStatus.PASS,
            message="Valid.",
            evidence_used=used
        )

class FaultyCheck(BaseCheck):
    @classmethod
    def key(cls) -> str:
        return "test.faulty_check"

    @classmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        return []

    def execute(self, package: EvidencePackage) -> CheckResult:
        raise ValueError("Unexpected failure!")


class TestCheckFramework(unittest.TestCase):
    
    def setUp(self):
        self.registry = CheckRegistry()
        self.executor = CheckExecutor(self.registry)
        
        self.receipt = TestReceiptEvidence(
            source="test", origin="test", collected_at=datetime.now(), reliability=Reliability.HIGH, amount=100.0
        )
        self.gps = TestGPSEvidence(
            source="test", origin="test", collected_at=datetime.now(), reliability=Reliability.HIGH, lat=1.0, lon=2.0
        )

    def test_check_registration_and_lookup(self):
        self.registry.register(ValidCheck)
        
        # Duplicate registration
        with self.assertRaises(ValueError):
            self.registry.register(ValidCheck)
            
        # Lookup
        cls = self.registry.get_check("ValidCheck")
        self.assertEqual(cls, ValidCheck)
        
        # Enumerate deterministic order
        self.registry.register(FaultyCheck)
        checks = self.registry.enumerate_checks()
        self.assertEqual(checks[0].name(), "FaultyCheck")
        self.assertEqual(checks[1].name(), "ValidCheck")

    def test_executor_missing_required_evidence(self):
        self.registry.register(ValidCheck)
        
        # Package without Receipt
        package = EvidencePackage([self.gps])
        results = self.executor.execute_all(package)
        
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.check_name, "ValidCheck")
        self.assertEqual(res.status, CheckStatus.SKIPPED)
        self.assertIn("Missing required evidence", res.message)

    def test_executor_missing_optional_evidence(self):
        self.registry.register(ValidCheck)
        
        # Package with Receipt, but no GPS
        package = EvidencePackage([self.receipt])
        results = self.executor.execute_all(package)
        
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.status, CheckStatus.PASS)
        self.assertIn("TestReceiptEvidence", res.evidence_used)
        self.assertNotIn("TestGPSEvidence", res.evidence_used)

    def test_executor_with_all_evidence(self):
        self.registry.register(ValidCheck)
        
        package = EvidencePackage([self.receipt, self.gps])
        results = self.executor.execute_all(package)
        
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.status, CheckStatus.PASS)
        self.assertIn("TestReceiptEvidence", res.evidence_used)
        self.assertIn("TestGPSEvidence", res.evidence_used)
        
    def test_executor_isolates_faults(self):
        self.registry.register(FaultyCheck)
        self.registry.register(ValidCheck)
        
        package = EvidencePackage([self.receipt])
        results = self.executor.execute_all(package)
        
        # FaultyCheck throws ValueError, ValidCheck should still pass
        self.assertEqual(len(results), 2)
        
        faulty_res = next(r for r in results if r.check_name == "FaultyCheck")
        valid_res = next(r for r in results if r.check_name == "ValidCheck")
        
        self.assertEqual(faulty_res.status, CheckStatus.ERROR)
        self.assertIn("Unhandled exception", faulty_res.message)
        self.assertIn("traceback", faulty_res.metadata)
        
        self.assertEqual(valid_res.status, CheckStatus.PASS)
