import unittest
import asyncio
from datetime import datetime

from schemas.validation_sdk import ValidationContext, RuleResult, RuleStatus, RuleSeverity, RuleCategory
from schemas.validation_result import ValidationVerdict
from schemas.operational_event import OperationalEventResponse, EventType, EntityType, CaptureMethod
from schemas.evidence_package import EvidencePackage
from infrastructure.validation.engine import ValidationEngine
from infrastructure.validation.registry import ValidationRuleRegistry
from infrastructure.validation.rules.example_fuel_structural_rule import ExampleFuelStructuralRule


class TestValidationEngineRegression(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.registry = ValidationRuleRegistry()
        self.registry.register(ExampleFuelStructuralRule())
        self.engine = ValidationEngine(self.registry)
        
        import uuid
        from models.operational_event import VerificationStatus
        self.base_event = OperationalEventResponse(
            id=uuid.uuid4(),
            event_type=EventType.FUEL_FILLED,
            entity_type=EntityType.VEHICLE,
            entity_id="1",
            occurred_at=datetime.now(),
            recorded_at=datetime.now(),
            capture_method=CaptureMethod.SYSTEM_GENERATED,
            verification_status=VerificationStatus.PENDING,
            created_by="test",
            payload={"liters": 50.0, "amount": 100.0, "odometer": 10000},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.base_package = EvidencePackage(event_id=self.base_event.id, collection_status="COMPLETED")

    def _build_context(self, payload=None):
        if payload is not None:
            self.base_event.payload = payload
            
        return ValidationContext(
            event=self.base_event,
            evidence_package=self.base_package,
            evidence_records=[],
            business_state={}
        )

    async def test_engine_processes_pass_status_correctly(self):
        ctx = self._build_context()
        
        result = await self.engine.evaluate(ctx)
        
        self.assertEqual(result.verdict, ValidationVerdict.VERIFIED)
        self.assertIn("example_fuel_structural_rule", result.passed_rules)
        self.assertEqual(len(result.failed_rules), 0)

    async def test_engine_processes_fail_status_correctly(self):
        # Trigger a failure by sending an empty payload
        ctx = self._build_context(payload={})
        
        result = await self.engine.evaluate(ctx)
        
        self.assertEqual(result.verdict, ValidationVerdict.REJECTED)
        self.assertNotIn("example_fuel_structural_rule", result.passed_rules)
        self.assertEqual(len(result.failed_rules), 1)
        self.assertEqual(result.failed_rules[0].status, RuleStatus.FAIL)

    async def test_engine_processes_skipped_status_correctly(self):
        # We need a mock rule that skips
        from infrastructure.validation.rule import BaseValidationRule
        class MockSkippedRule(BaseValidationRule):
            @property
            def name(self) -> str: return "mock_skip"
            @property
            def category(self) -> RuleCategory: return RuleCategory.BUSINESS_LOGIC
            @property
            def priority(self) -> int: return 150
            def applies_to(self, ctx) -> bool: return True
            async def evaluate(self, ctx) -> RuleResult:
                return RuleResult(rule_name=self.name, status=RuleStatus.SKIPPED, severity=RuleSeverity.INFO, message="skip")

        registry = ValidationRuleRegistry()
        registry.register(MockSkippedRule())
        engine = ValidationEngine(registry)

        result = await engine.evaluate(self._build_context())
        
        # SKIPPED should not reject, nor dispute, just bypass.
        self.assertEqual(result.verdict, ValidationVerdict.VERIFIED)
        self.assertEqual(len(result.passed_rules), 0)
        self.assertEqual(len(result.failed_rules), 0)
        self.assertEqual(len(result.warnings), 0) # wait, engine currently logs skipped, doesn't add to warnings. Let's verify.
