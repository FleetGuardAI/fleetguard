import unittest
from datetime import datetime, timedelta, timezone

from infrastructure.intelligence.evidence.models import (
    VehicleRegistrationEvidence, InsuranceEvidence, FitnessCertificateEvidence,
    PollutionCertificateEvidence, PermitEvidence, DriverLicenseEvidence, Reliability
)
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.models import CheckStatus
from infrastructure.intelligence.compliance_domain.config import ComplianceIntelligenceConfig
from infrastructure.intelligence.compliance_domain.checks.registration import RegistrationValidityCheck
from infrastructure.intelligence.compliance_domain.checks.insurance import InsuranceValidityCheck
from infrastructure.intelligence.compliance_domain.checks.fitness import FitnessCertificateCheck
from infrastructure.intelligence.compliance_domain.checks.pollution import PollutionCertificateCheck
from infrastructure.intelligence.compliance_domain.checks.permit import PermitValidityCheck
from infrastructure.intelligence.compliance_domain.checks.driver_license import DriverLicenseValidityCheck


class TestComplianceChecks(unittest.TestCase):
    def setUp(self):
        self.config = ComplianceIntelligenceConfig()
        self.now = datetime.now(timezone.utc)
        self.past = self.now - timedelta(days=10)
        self.future = self.now + timedelta(days=50)
        self.warning_future = self.now + timedelta(days=10)

    def test_registration_validity_check(self):
        check = RegistrationValidityCheck(self.config)
        
        # Pass
        ev = VehicleRegistrationEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="REG123", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.future, jurisdiction="STATE"
        )
        res = check.execute(EvidencePackage([ev]))
        self.assertEqual(res.status, CheckStatus.PASS)
        self.assertFalse(res.metadata.get("expiring_soon"))
        
        # Warning (still pass)
        ev_warning = VehicleRegistrationEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="REG123", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.warning_future, jurisdiction="STATE"
        )
        res = check.execute(EvidencePackage([ev_warning]))
        self.assertEqual(res.status, CheckStatus.PASS)
        self.assertTrue(res.metadata.get("expiring_soon"))
        
        # Fail
        ev_fail = VehicleRegistrationEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="REG123", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.past, jurisdiction="STATE"
        )
        res = check.execute(EvidencePackage([ev_fail]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_insurance_validity_check(self):
        check = InsuranceValidityCheck(self.config)
        
        # Pass
        ev = InsuranceEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="INS123", issuing_authority="INS",
            issue_date=self.past, expiry_date=self.future, document_category="COMPREHENSIVE",
            document_status="ACTIVE"
        )
        res = check.execute(EvidencePackage([ev]))
        self.assertEqual(res.status, CheckStatus.PASS)
        
        # Fail Status
        ev_fail_status = InsuranceEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="INS123", issuing_authority="INS",
            issue_date=self.past, expiry_date=self.future, document_category="COMPREHENSIVE",
            document_status="REVOKED"
        )
        res = check.execute(EvidencePackage([ev_fail_status]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_fitness_validity_check(self):
        check = FitnessCertificateCheck(self.config)
        
        # Pass
        ev = FitnessCertificateEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="FIT123", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.future, document_status="ACTIVE"
        )
        res = check.execute(EvidencePackage([ev]))
        self.assertEqual(res.status, CheckStatus.PASS)
        
        # Fail expired
        ev_fail = FitnessCertificateEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="FIT123", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.past, document_status="ACTIVE"
        )
        res = check.execute(EvidencePackage([ev_fail]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_pollution_validity_check(self):
        check = PollutionCertificateCheck(self.config)
        
        # Pass
        ev = PollutionCertificateEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="POL123", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.future
        )
        res = check.execute(EvidencePackage([ev]))
        self.assertEqual(res.status, CheckStatus.PASS)
        
        # Fail expired
        ev_fail = PollutionCertificateEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="POL123", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.past
        )
        res = check.execute(EvidencePackage([ev_fail]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_permit_validity_check(self):
        check = PermitValidityCheck(self.config)
        
        ev_national = PermitEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="PER1", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.future, document_category="NATIONAL", jurisdiction="IN"
        )
        
        ev_state = PermitEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="PER2", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.future, document_category="STATE", jurisdiction="MH"
        )
        
        # Pass
        res = check.execute(EvidencePackage([ev_national, ev_state]))
        self.assertEqual(res.status, CheckStatus.PASS)
        
        # Fail missing mandatory
        res = check.execute(EvidencePackage([ev_national]))
        self.assertEqual(res.status, CheckStatus.FAIL)
        self.assertIn("STATE", res.metadata["missing_permits"])
        
        # Fail expired
        ev_state_expired = PermitEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            vehicle_id="v1", document_number="PER2", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.past, document_category="STATE", jurisdiction="MH"
        )
        res = check.execute(EvidencePackage([ev_national, ev_state_expired]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_driver_license_validity_check(self):
        check = DriverLicenseValidityCheck(self.config)
        
        # Pass
        ev = DriverLicenseEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            driver_id="d1", document_number="DL123", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.future, document_category="COMMERCIAL", jurisdiction="STATE"
        )
        res = check.execute(EvidencePackage([ev]))
        self.assertEqual(res.status, CheckStatus.PASS)
        
        # Fail class
        ev_fail = DriverLicenseEvidence(
            source="system", origin="api", collected_at=self.now, reliability=Reliability.HIGH,
            driver_id="d1", document_number="DL123", issuing_authority="RTO",
            issue_date=self.past, expiry_date=self.future, document_category="CAR", jurisdiction="STATE"
        )
        res = check.execute(EvidencePackage([ev_fail]))
        self.assertEqual(res.status, CheckStatus.FAIL)
