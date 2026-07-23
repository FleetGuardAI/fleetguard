import unittest
from datetime import datetime, timezone, timedelta

from infrastructure.intelligence.evidence.models import ReceiptEvidence, GPSEvidence, FuelSensorEvidence, VehicleEvidence, Reliability
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.registry import CheckRegistry
from infrastructure.intelligence.checks.executor import CheckExecutor
from infrastructure.intelligence.assessments.registry import AssessmentRegistry
from infrastructure.intelligence.assessments.executor import AssessmentExecutor
from infrastructure.intelligence.domain_risk.registry import DomainRiskRegistry
from infrastructure.intelligence.domain_risk.executor import DomainRiskExecutor
from infrastructure.intelligence.global_decision.registry import DecisionRegistry
from infrastructure.intelligence.global_decision.executor import DecisionExecutor

# Fuel Domain Implementations
from infrastructure.intelligence.fuel_domain.config import FuelIntelligenceConfig
from infrastructure.intelligence.fuel_domain.checks.quantity import FuelQuantityCheck
from infrastructure.intelligence.fuel_domain.checks.location import FuelLocationCheck
from infrastructure.intelligence.fuel_domain.checks.timing import FuelTimingCheck
from infrastructure.intelligence.fuel_domain.checks.tank_capacity import FuelTankCapacityCheck
from infrastructure.intelligence.fuel_domain.assessments.transaction_integrity import FuelTransactionIntegrityAssessment
from infrastructure.intelligence.fuel_domain.risk.transaction_risk import FuelTransactionRiskEngine
from infrastructure.intelligence.fuel_domain.decision.transaction_decision import FuelDecisionEngine
from infrastructure.intelligence.global_decision.models import RecommendationStatus


class TestFuelIntelligencePipeline(unittest.TestCase):
    def setUp(self):
        # 1. Setup Framework Registries and Executors
        self.check_registry = CheckRegistry()
        self.check_registry.register(FuelQuantityCheck)
        self.check_registry.register(FuelLocationCheck)
        self.check_registry.register(FuelTimingCheck)
        self.check_registry.register(FuelTankCapacityCheck)
        self.check_executor = CheckExecutor(self.check_registry)

        self.assessment_registry = AssessmentRegistry()
        self.assessment_registry.register(FuelTransactionIntegrityAssessment)
        self.assessment_executor = AssessmentExecutor(self.assessment_registry)

        self.risk_registry = DomainRiskRegistry()
        self.risk_registry.register(FuelTransactionRiskEngine)
        self.risk_executor = DomainRiskExecutor(self.risk_registry)

        self.decision_registry = DecisionRegistry()
        self.decision_registry.register(FuelDecisionEngine)
        self.decision_executor = DecisionExecutor(self.decision_registry)

        # 2. Setup Base Evidence
        now = datetime.now(timezone.utc)
        
        self.receipt = ReceiptEvidence(
            source="ocr", origin="receipt_scan", collected_at=now, reliability=Reliability.HIGH,
            quantity=100.0, amount=150.0, station_name="Test Station",
            metadata={"station_lat": 40.0, "station_lon": -74.0}
        )
        
        self.gps = GPSEvidence(
            source="telematics", origin="truck_gps", collected_at=now, reliability=Reliability.HIGH,
            latitude=40.0, longitude=-74.0, accuracy=5.0
        )
        
        self.sensor = FuelSensorEvidence(
            source="canbus", origin="fuel_sensor", collected_at=now, reliability=Reliability.HIGH,
            fuel_before=50.0, fuel_after=150.0
        )
        
        self.vehicle = VehicleEvidence(
            source="fleet_api", origin="master_data", collected_at=now, reliability=Reliability.VERIFIED,
            vehicle_id="TRK-001", tank_capacity=300.0
        )
        
        self.base_evidence = [self.receipt, self.gps, self.sensor, self.vehicle]

    def execute_pipeline(self, evidence):
        package = EvidencePackage(evidence)
        checks = self.check_executor.execute_all(package)
        assessments = self.assessment_executor.execute_all(checks)
        risks = self.risk_executor.execute_all(assessments)
        decisions = self.decision_executor.execute_all(risks)
        return decisions[0]

    def test_pipeline_valid_transaction(self):
        """End-to-End Test: Perfect transaction -> APPROVE"""
        final_decision = self.execute_pipeline(self.base_evidence)
        self.assertEqual(final_decision.recommendation, RecommendationStatus.APPROVE)
        
        # Verify Explainability Tree
        self.assertEqual(len(final_decision.supporting_profiles), 1)
        risk = final_decision.supporting_profiles[0]
        self.assertEqual(risk.risk_level.value, "LOW")
        
        self.assertEqual(len(risk.supporting_assessments), 1)
        assessment = risk.supporting_assessments[0]
        self.assertEqual(assessment.status.value, "COMPLETE")
        
        self.assertEqual(len(assessment.contributing_checks), 4)
        for check in assessment.contributing_checks:
            self.assertEqual(check.status.value, "PASS")

    def test_pipeline_quantity_mismatch(self):
        """End-to-End Test: Quantity mismatch -> CRITICAL or HIGH -> REJECT or REVIEW_REQUIRED"""
        # Inject bad receipt quantity (100L receipt vs 50L actually filled: fuel_after=100)
        bad_sensor = self.sensor.model_copy(update={"fuel_after": 100.0})
        evidence = [self.receipt, self.gps, bad_sensor, self.vehicle]
        
        final_decision = self.execute_pipeline(evidence)
        
        # A single check failure means 1 mismatch -> HIGH risk -> REVIEW_REQUIRED
        self.assertEqual(final_decision.recommendation, RecommendationStatus.REVIEW_REQUIRED)

    def test_pipeline_multiple_mismatches(self):
        """End-to-End Test: Multiple failures -> CRITICAL risk -> REJECT"""
        bad_sensor = self.sensor.model_copy(update={"fuel_after": 100.0})
        # Bad GPS location (different lat/lon) -> haversine distance will be large
        bad_gps = self.gps.model_copy(update={"latitude": 41.0, "longitude": -75.0})
        evidence = [self.receipt, bad_gps, bad_sensor, self.vehicle]
        
        final_decision = self.execute_pipeline(evidence)
        
        self.assertEqual(final_decision.recommendation, RecommendationStatus.REJECT)

    def test_pipeline_missing_evidence(self):
        """End-to-End Test: Missing GPS -> SKIPPED checks -> INCONCLUSIVE assessment -> INCONCLUSIVE risk -> None recommendation"""
        # Remove GPS
        evidence = [self.receipt, self.sensor, self.vehicle]
        
        final_decision = self.execute_pipeline(evidence)
        
        self.assertEqual(final_decision.status.value, "INCONCLUSIVE")
        self.assertIsNone(final_decision.recommendation)
