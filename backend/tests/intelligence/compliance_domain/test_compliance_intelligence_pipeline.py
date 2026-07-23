import unittest
from datetime import datetime, timedelta, timezone

from infrastructure.intelligence.evidence.models import (
    VehicleRegistrationEvidence, InsuranceEvidence, FitnessCertificateEvidence,
    PollutionCertificateEvidence, PermitEvidence, DriverLicenseEvidence, Reliability
)
from infrastructure.intelligence.evidence.package import EvidencePackage

from infrastructure.intelligence.orchestrator.base import IntelligenceOrchestrator
from infrastructure.intelligence.checks.registry import CheckRegistry
from infrastructure.intelligence.checks.executor import CheckExecutor
from infrastructure.intelligence.assessments.registry import AssessmentRegistry
from infrastructure.intelligence.assessments.executor import AssessmentExecutor
from infrastructure.intelligence.domain_risk.registry import DomainRiskRegistry
from infrastructure.intelligence.domain_risk.executor import DomainRiskExecutor
from infrastructure.intelligence.global_decision.registry import DecisionRegistry
from infrastructure.intelligence.global_decision.executor import DecisionExecutor
from infrastructure.intelligence.orchestrator.models import IntelligenceExecutionStatus

from infrastructure.intelligence.compliance_domain.checks.registration import RegistrationValidityCheck
from infrastructure.intelligence.compliance_domain.checks.insurance import InsuranceValidityCheck
from infrastructure.intelligence.compliance_domain.checks.fitness import FitnessCertificateCheck
from infrastructure.intelligence.compliance_domain.checks.pollution import PollutionCertificateCheck
from infrastructure.intelligence.compliance_domain.checks.permit import PermitValidityCheck
from infrastructure.intelligence.compliance_domain.checks.driver_license import DriverLicenseValidityCheck
from infrastructure.intelligence.compliance_domain.assessments.vehicle_compliance import VehicleComplianceAssessment
from infrastructure.intelligence.compliance_domain.risk.vehicle_compliance_risk import VehicleComplianceRiskEngine
from infrastructure.intelligence.compliance_domain.decision.vehicle_compliance_decision import VehicleComplianceDecisionEngine
from infrastructure.intelligence.global_decision.models import RecommendationStatus


class TestCompliancePipeline(unittest.TestCase):
    def setUp(self):
        check_registry = CheckRegistry()
        check_registry.register(RegistrationValidityCheck)
        check_registry.register(InsuranceValidityCheck)
        check_registry.register(FitnessCertificateCheck)
        check_registry.register(PollutionCertificateCheck)
        check_registry.register(PermitValidityCheck)
        check_registry.register(DriverLicenseValidityCheck)
        check_executor = CheckExecutor(check_registry)
        
        assessment_registry = AssessmentRegistry()
        assessment_registry.register(VehicleComplianceAssessment)
        assessment_executor = AssessmentExecutor(assessment_registry)
        
        risk_registry = DomainRiskRegistry()
        risk_registry.register(VehicleComplianceRiskEngine)
        risk_executor = DomainRiskExecutor(risk_registry)
        
        decision_registry = DecisionRegistry()
        decision_registry.register(VehicleComplianceDecisionEngine)
        decision_executor = DecisionExecutor(decision_registry)
        
        self.orchestrator = IntelligenceOrchestrator(
            check_executor=check_executor,
            assessment_executor=assessment_executor,
            risk_executor=risk_executor,
            decision_executor=decision_executor
        )
        
        self.now = datetime.now(timezone.utc)
        self.past = self.now - timedelta(days=10)
        self.future = self.now + timedelta(days=50)

    def _get_base_evidence(self):
        return [
            VehicleRegistrationEvidence(
                source="sys", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
                vehicle_id="v1", document_number="REG1", issuing_authority="RTO",
                issue_date=self.past, expiry_date=self.future, jurisdiction="STATE"
            ),
            InsuranceEvidence(
                source="sys", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
                vehicle_id="v1", document_number="INS1", issuing_authority="INS",
                issue_date=self.past, expiry_date=self.future, document_category="COMPREHENSIVE",
                document_status="ACTIVE"
            ),
            FitnessCertificateEvidence(
                source="sys", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
                vehicle_id="v1", document_number="FIT1", issuing_authority="RTO",
                issue_date=self.past, expiry_date=self.future, document_status="ACTIVE"
            ),
            PollutionCertificateEvidence(
                source="sys", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
                vehicle_id="v1", document_number="POL1", issuing_authority="RTO",
                issue_date=self.past, expiry_date=self.future
            ),
            PermitEvidence(
                source="sys", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
                vehicle_id="v1", document_number="PER1", issuing_authority="RTO",
                issue_date=self.past, expiry_date=self.future, document_category="NATIONAL", jurisdiction="IN"
            ),
            PermitEvidence(
                source="sys", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
                vehicle_id="v1", document_number="PER2", issuing_authority="RTO",
                issue_date=self.past, expiry_date=self.future, document_category="STATE", jurisdiction="MH"
            ),
            DriverLicenseEvidence(
                source="sys", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
                driver_id="d1", document_number="DL1", issuing_authority="RTO",
                issue_date=self.past, expiry_date=self.future, document_category="COMMERCIAL", jurisdiction="STATE"
            )
        ]

    def test_end_to_end_compliant_vehicle(self):
        evs = self._get_base_evidence()
        result = self.orchestrator.execute(EvidencePackage(evs))
        
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.APPROVE)
        
    def test_end_to_end_critical_vehicle(self):
        evs = self._get_base_evidence()
        # Expire insurance
        evs[1] = InsuranceEvidence(
            source="sys", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="INS1", issuing_authority="INS",
            issue_date=self.past, expiry_date=self.past, document_category="COMPREHENSIVE",
            document_status="ACTIVE"
        )
        
        result = self.orchestrator.execute(EvidencePackage(evs))
        self.assertEqual(result.status, IntelligenceExecutionStatus.COMPLETE)
        self.assertEqual(result.recommendations[0].recommendation, RecommendationStatus.REJECT)
