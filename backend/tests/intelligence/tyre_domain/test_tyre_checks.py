import unittest
from datetime import datetime, timedelta, timezone

from infrastructure.intelligence.evidence.models import (
    TyreInspectionEvidence,
    TyrePressureEvidence,
    Reliability,
    TyrePosition,
    WearPatternCategory,
    DamageSeverity
)
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.models import CheckStatus
from infrastructure.intelligence.tyre_domain.config import TyreIntelligenceConfig
from infrastructure.intelligence.tyre_domain.checks.pressure import TyrePressureCheck
from infrastructure.intelligence.tyre_domain.checks.tread_depth import TyreTreadDepthCheck
from infrastructure.intelligence.tyre_domain.checks.age import TyreAgeCheck
from infrastructure.intelligence.tyre_domain.checks.wear_pattern import TyreWearPatternCheck
from infrastructure.intelligence.tyre_domain.checks.damage import TyreDamageCheck


class TestTyreChecks(unittest.TestCase):
    def setUp(self):
        self.config = TyreIntelligenceConfig()
        self.now = datetime.now(timezone.utc)
        
        self.inspection = TyreInspectionEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            tyre_position=TyrePosition.FRONT_LEFT,
            inspection_date=self.now,
            tread_depth_mm=4.0,
            tyre_installation_date=self.now - timedelta(days=365),
            wear_pattern=WearPatternCategory.NORMAL,
            observed_damage_severity=DamageSeverity.NONE
        )
        
        self.pressure = TyrePressureEvidence(
            source="test", origin="test", collected_at=self.now,
            reliability=Reliability.HIGH,
            vehicle_id="v1",
            tyre_position=TyrePosition.FRONT_LEFT,
            reading_date=self.now,
            tyre_pressure_psi=32.0,
            recommended_pressure_psi=32.0
        )
        
        self.package = EvidencePackage([self.inspection, self.pressure])

    def test_pressure_pass(self):
        check = TyrePressureCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_pressure_fail(self):
        check = TyrePressureCheck(self.config)
        bad_pressure = self.pressure.model_copy(deep=True, update={"tyre_pressure_psi": 25.0}) # Dev = 7 > 5
        res = check.execute(EvidencePackage([self.inspection, bad_pressure]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_tread_depth_pass(self):
        check = TyreTreadDepthCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_tread_depth_fail(self):
        check = TyreTreadDepthCheck(self.config)
        bad_inspection = self.inspection.model_copy(deep=True, update={"tread_depth_mm": 1.5}) # Min is 2.0
        res = check.execute(EvidencePackage([bad_inspection, self.pressure]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_age_pass(self):
        check = TyreAgeCheck(self.config)
        res = check.execute(self.package) # 1 year old
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_age_fail(self):
        check = TyreAgeCheck(self.config)
        bad_inspection = self.inspection.model_copy(deep=True, update={"tyre_installation_date": self.now - timedelta(days=2000)}) # Max 1825
        res = check.execute(EvidencePackage([bad_inspection, self.pressure]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_wear_pattern_pass(self):
        check = TyreWearPatternCheck(self.config)
        res = check.execute(self.package)
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_wear_pattern_fail(self):
        check = TyreWearPatternCheck(self.config)
        bad_inspection = self.inspection.model_copy(deep=True, update={"wear_pattern": WearPatternCategory.UNEVEN})
        res = check.execute(EvidencePackage([bad_inspection, self.pressure]))
        self.assertEqual(res.status, CheckStatus.FAIL)

    def test_damage_pass(self):
        check = TyreDamageCheck(self.config)
        # test with MINOR damage (not CRITICAL)
        minor_inspection = self.inspection.model_copy(deep=True, update={"observed_damage_severity": DamageSeverity.MINOR})
        res = check.execute(EvidencePackage([minor_inspection, self.pressure]))
        self.assertEqual(res.status, CheckStatus.PASS)

    def test_damage_fail(self):
        check = TyreDamageCheck(self.config)
        bad_inspection = self.inspection.model_copy(deep=True, update={"observed_damage_severity": DamageSeverity.CRITICAL})
        res = check.execute(EvidencePackage([bad_inspection, self.pressure]))
        self.assertEqual(res.status, CheckStatus.FAIL)
