import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from models.fuel_root_cause import RootCauseType, EvidenceStatus, EvidenceStrength
from models.derived_fuel_metrics import EntityTypeEnum
from infrastructure.intelligence.core.contributing_factors import GenericContributingFactorEngine, EvidenceResult
from infrastructure.intelligence.core.provider import BaseContributingFactorProvider

class DummyAnomaly:
    def __init__(self):
        self.entity_id = "TEST-1"
        self.entity_type = EntityTypeEnum.TRUCK
        self.observation_reference = "obs-123"
        self.period_start = datetime(2026, 8, 1, tzinfo=timezone.utc)
        self.period_end = datetime(2026, 8, 2, tzinfo=timezone.utc)

class DummyImpact:
    def __init__(self):
        self.anomaly_reference = "imp-456"

class MockProvider(BaseContributingFactorProvider):
    def __init__(self, result: EvidenceResult | None):
        self._result = result
        
    async def evaluate(self, uow, anomaly, impact):
        return self._result

@pytest.mark.asyncio
async def test_no_evidence_fallback_to_unknown():
    engine = GenericContributingFactorEngine()
    
    # Provider returns NEUTRAL evidence
    provider1 = MockProvider(EvidenceResult(
        factor_type=RootCauseType.HIGH_SPEED,
        evidence_status=EvidenceStatus.NEUTRAL,
        evidence_strength=EvidenceStrength.NO_EVIDENCE,
        explanation="No speed issues."
    ))
    
    # Provider returns nothing
    provider2 = MockProvider(None)
    
    anomaly = DummyAnomaly()
    impact = DummyImpact()
    
    result = await engine.evaluate_providers(None, anomaly, impact, [provider1, provider2])
    
    assert result.status == "SUCCESS"
    assert result.entity_id == "TEST-1"
    
    factors = result.contributing_factors
    assert len(factors) == 2  # UNKNOWN fallback + the NEUTRAL one
    
    assert factors[0].factor_type == RootCauseType.UNKNOWN
    assert factors[0].evidence_status == EvidenceStatus.UNAVAILABLE
    assert factors[0].evidence_strength == EvidenceStrength.NO_EVIDENCE

@pytest.mark.asyncio
async def test_deterministic_ranking_by_strength_and_type():
    engine = GenericContributingFactorEngine()
    
    # We create several providers with varying strengths and factor types
    # Expected order: STRONG (SPEED) -> MODERATE (MAINTENANCE) -> WEAK (DISTANCE) -> NO_EVIDENCE (IDLE)
    
    p1 = MockProvider(EvidenceResult(
        factor_type=RootCauseType.EXCESS_DISTANCE,
        evidence_status=EvidenceStatus.SUPPORTING,
        evidence_strength=EvidenceStrength.WEAK_SUPPORT,
        explanation="Weak support"
    ))
    
    p2 = MockProvider(EvidenceResult(
        factor_type=RootCauseType.VEHICLE_MAINTENANCE,
        evidence_status=EvidenceStatus.SUPPORTING,
        evidence_strength=EvidenceStrength.MODERATE_SUPPORT,
        explanation="Moderate support"
    ))
    
    p3 = MockProvider(EvidenceResult(
        factor_type=RootCauseType.HIGH_SPEED,
        evidence_status=EvidenceStatus.SUPPORTING,
        evidence_strength=EvidenceStrength.STRONG_SUPPORT,
        explanation="Strong support"
    ))
    
    p4 = MockProvider(EvidenceResult(
        factor_type=RootCauseType.EXCESSIVE_IDLE,
        evidence_status=EvidenceStatus.NEUTRAL,
        evidence_strength=EvidenceStrength.NO_EVIDENCE,
        explanation="No support"
    ))
    
    # A tie in strength to test secondary sorting by factor_type name alphabetically
    # EXCESS_DISTANCE vs FUEL_EVENT_ANOMALY (both STRONG)
    p5 = MockProvider(EvidenceResult(
        factor_type=RootCauseType.FUEL_EVENT_ANOMALY,
        evidence_status=EvidenceStatus.SUPPORTING,
        evidence_strength=EvidenceStrength.STRONG_SUPPORT,
        explanation="Strong tie"
    ))
    
    result = await engine.evaluate_providers(None, DummyAnomaly(), None, [p1, p2, p3, p4, p5])
    
    factors = result.contributing_factors
    # We should have no UNKNOWN fallback because there is SUPPORTING evidence
    assert len(factors) == 5
    
    # 1. FUEL_EVENT_ANOMALY (STRONG, alphabetically before HIGH_SPEED)
    assert factors[0].factor_type == RootCauseType.FUEL_EVENT_ANOMALY
    assert factors[0].evidence_strength == EvidenceStrength.STRONG_SUPPORT
    
    # 2. HIGH_SPEED (STRONG)
    assert factors[1].factor_type == RootCauseType.HIGH_SPEED
    assert factors[1].evidence_strength == EvidenceStrength.STRONG_SUPPORT
    
    # 3. VEHICLE_MAINTENANCE (MODERATE)
    assert factors[2].factor_type == RootCauseType.VEHICLE_MAINTENANCE
    assert factors[2].evidence_strength == EvidenceStrength.MODERATE_SUPPORT
    
    # 4. EXCESS_DISTANCE (WEAK)
    assert factors[3].factor_type == RootCauseType.EXCESS_DISTANCE
    assert factors[3].evidence_strength == EvidenceStrength.WEAK_SUPPORT
    
    # 5. EXCESSIVE_IDLE (NO_EVIDENCE)
    assert factors[4].factor_type == RootCauseType.EXCESSIVE_IDLE
    assert factors[4].evidence_strength == EvidenceStrength.NO_EVIDENCE
