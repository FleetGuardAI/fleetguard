import unittest
from datetime import datetime
import asyncio

from schemas.validation_sdk import ValidationContext, RuleStatus, RuleSeverity
from schemas.operational_event import OperationalEventResponse, EventType, EntityType, CaptureMethod
from schemas.evidence_package import EvidencePackage
from schemas.fuel_domain import CurrentFuelState
from models.fuel_domain import FuelSource, FuelStateReliability
from infrastructure.validation.rules.tank_capacity_rule import TankCapacityRule


class TestTankCapacityRule(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.rule = TankCapacityRule()
        
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
            payload={"liters": 50.0},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.base_package = EvidencePackage(event_id=self.base_event.id, collection_status="COMPLETED")
        self.base_fuel_state = CurrentFuelState(
            vehicle_id=1,
            current_fuel_liters=100.0,
            capacity_liters=200.0,
            source=FuelSource.SENSOR,
            reliability=FuelStateReliability.HIGH,
            last_updated=datetime.now()
        )

    def _build_context(self, payload=None, fuel_state=None, remove_fuel_state=False):
        if payload is not None:
            self.base_event.payload = payload
        
        business_state = {}
        if not remove_fuel_state:
            business_state["current_fuel_state"] = fuel_state or self.base_fuel_state

        return ValidationContext(
            event=self.base_event,
            evidence_package=self.base_package,
            evidence_records=[],
            business_state=business_state
        )

    async def test_applies_to_fuel_filled_only(self):
        ctx = self._build_context()
        self.assertTrue(self.rule.applies_to(ctx))
        
        ctx.event.event_type = EventType.TRIP_STARTED
        self.assertFalse(self.rule.applies_to(ctx))

    async def test_valid_fuel_fill_pass(self):
        ctx = self._build_context()
        result = await self.rule.evaluate(ctx)
        
        self.assertEqual(result.status, RuleStatus.PASS)
        self.assertEqual(result.severity, RuleSeverity.INFO)
        self.assertEqual(result.metadata["fuel_after_fill"], 150.0)

    async def test_exact_tank_capacity_pass(self):
        ctx = self._build_context(payload={"liters": 100.0}) # 100 + 100 = 200 (capacity)
        result = await self.rule.evaluate(ctx)
        
        self.assertEqual(result.status, RuleStatus.PASS)
        self.assertEqual(result.metadata["fuel_after_fill"], 200.0)

    async def test_overflow_fail(self):
        ctx = self._build_context(payload={"liters": 150.0}) # 100 + 150 = 250 > 200
        result = await self.rule.evaluate(ctx)
        
        self.assertEqual(result.status, RuleStatus.FAIL)
        self.assertEqual(result.severity, RuleSeverity.CRITICAL)
        self.assertEqual(result.metadata["overflow_liters"], 50.0)

    async def test_empty_tank_fill_pass(self):
        empty_state = self.base_fuel_state.model_copy(update={"current_fuel_liters": 0.0})
        ctx = self._build_context(payload={"liters": 200.0}, fuel_state=empty_state)
        result = await self.rule.evaluate(ctx)
        
        self.assertEqual(result.status, RuleStatus.PASS)

    async def test_full_tank_fill_fail(self):
        full_state = self.base_fuel_state.model_copy(update={"current_fuel_liters": 200.0})
        ctx = self._build_context(payload={"liters": 10.0}, fuel_state=full_state)
        result = await self.rule.evaluate(ctx)
        
        self.assertEqual(result.status, RuleStatus.FAIL)
        self.assertEqual(result.metadata["overflow_liters"], 10.0)

    async def test_missing_fuel_state_skipped(self):
        ctx = self._build_context(remove_fuel_state=True)
        result = await self.rule.evaluate(ctx)
        
        self.assertEqual(result.status, RuleStatus.SKIPPED)
        self.assertIn("CurrentFuelState is missing", result.message)

    async def test_missing_claimed_quantity_skipped(self):
        ctx = self._build_context(payload={"other": "data"})
        result = await self.rule.evaluate(ctx)
        
        self.assertEqual(result.status, RuleStatus.SKIPPED)
        self.assertIn("missing from the event payload", result.message)

    async def test_negative_claimed_quantity_pass_or_fail(self):
        # Even though structural validation catches negative numbers, 
        # the business rule must handle it mathematically correct. 
        # Adding negative fuel reduces the fuel level, so it fits in the tank.
        # It's an invalid 'fill', but physically it doesn't exceed capacity.
        # We test that it evaluates gracefully.
        ctx = self._build_context(payload={"liters": -50.0})
        result = await self.rule.evaluate(ctx)
        
        # 100 - 50 = 50 <= 200 -> PASS for capacity rule
        self.assertEqual(result.status, RuleStatus.PASS)

    async def test_invalid_type_claimed_quantity_error(self):
        ctx = self._build_context(payload={"liters": "fifty"})
        result = await self.rule.evaluate(ctx)
        
        self.assertEqual(result.status, RuleStatus.ERROR)
        self.assertEqual(result.severity, RuleSeverity.CRITICAL)
