"""
FleetGuard — Generic Contributing Factors Core
"""

from typing import List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from models.fuel_root_cause import RootCauseType, EvidenceStatus, EvidenceStrength
from models.derived_fuel_metrics import EntityTypeEnum

@dataclass
class EvidenceResult:
    """Generic contract for evidence produced by any domain provider."""
    factor_type: RootCauseType
    evidence_status: EvidenceStatus
    evidence_strength: EvidenceStrength
    explanation: str
    evidence_value: Optional[float] = None
    baseline_value: Optional[float] = None
    deviation_percent: Optional[float] = None
    unit: Optional[str] = None
    source_references: Optional[str] = None

@dataclass
class ContributingFactorAnalysisResult:
    """Generic output of the contributing factor engine."""
    status: str
    entity_id: str
    entity_type: EntityTypeEnum
    anomaly_reference: str
    financial_impact_reference: Optional[str]
    period_start: datetime
    period_end: datetime
    contributing_factors: List[EvidenceResult] = field(default_factory=list)


class GenericContributingFactorEngine:
    """
    Domain-agnostic engine that takes an anomaly, an optional financial impact,
    and a list of providers to evaluate evidence and rank them deterministically.
    """
    
    def _strength_to_rank(self, strength: EvidenceStrength) -> int:
        mapping = {
            EvidenceStrength.STRONG_SUPPORT: 3,
            EvidenceStrength.MODERATE_SUPPORT: 2,
            EvidenceStrength.WEAK_SUPPORT: 1,
            EvidenceStrength.NO_EVIDENCE: 0
        }
        return mapping.get(strength, 0)
        
    async def evaluate_providers(self, uow, anomaly, impact, providers) -> ContributingFactorAnalysisResult:
        evidence_results: List[EvidenceResult] = []
        for provider in providers:
            result = await provider.evaluate(uow, anomaly, impact)
            if result:
                evidence_results.append(result)
                
        # Deterministic Ranking
        # Primary: Strength (STRONG > MODERATE > WEAK > NO)
        # Secondary: factor_type (Alphabetical fallback)
        evidence_results.sort(
            key=lambda x: (-self._strength_to_rank(x.evidence_strength), x.factor_type.value)
        )
        
        # Check if we have any supporting evidence
        has_support = any(r.evidence_status == EvidenceStatus.SUPPORTING for r in evidence_results)
        
        if not has_support:
            # Fallback to UNKNOWN
            evidence_results.insert(0, 
                EvidenceResult(
                    factor_type=RootCauseType.UNKNOWN,
                    evidence_status=EvidenceStatus.UNAVAILABLE,
                    evidence_strength=EvidenceStrength.NO_EVIDENCE,
                    explanation="Anomaly detected, but available FleetGuard data does not provide sufficient evidence to identify a contributing factor."
                )
            )
            
        return ContributingFactorAnalysisResult(
            status="SUCCESS",
            entity_id=anomaly.entity_id,
            entity_type=anomaly.entity_type,
            anomaly_reference=anomaly.observation_reference,
            financial_impact_reference=impact.anomaly_reference if impact else None,
            period_start=anomaly.period_start,
            period_end=anomaly.period_end,
            contributing_factors=evidence_results
        )
