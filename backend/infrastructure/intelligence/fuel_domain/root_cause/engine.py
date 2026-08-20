from infrastructure.uow import AbstractUnitOfWork
from models.fuel_anomaly import FuelAnomaly
from models.fuel_financial_impact import FuelFinancialImpact
from models.fuel_root_cause import ContributingFactorAnalysis, ContributingFactorEvidence
from infrastructure.intelligence.core.contributing_factors import GenericContributingFactorEngine

from infrastructure.intelligence.fuel_domain.root_cause.providers.fuel_event import FuelEventEvidenceProvider
from infrastructure.intelligence.fuel_domain.root_cause.providers.speed import SpeedEvidenceProvider
from infrastructure.intelligence.fuel_domain.root_cause.providers.maintenance import MaintenanceEvidenceProvider
from infrastructure.intelligence.fuel_domain.root_cause.providers.excess_distance import ExcessDistanceEvidenceProvider

class FuelRootCauseEngine:
    """
    Acts as a domain-specific adapter that orchestrates Fuel providers
    and uses the GenericContributingFactorEngine to rank and fallback.
    """
    def __init__(self):
        self.providers = [
            FuelEventEvidenceProvider(),
            SpeedEvidenceProvider(),
            MaintenanceEvidenceProvider(),
            ExcessDistanceEvidenceProvider()
        ]
        self.generic_engine = GenericContributingFactorEngine()

    async def analyze_root_cause(
        self,
        uow: AbstractUnitOfWork,
        anomaly: FuelAnomaly,
        impact: FuelFinancialImpact | None = None
    ):
        # 1. Execute Generic Engine which will evaluate providers, rank, and handle UNKNOWN
        analysis_result = await self.generic_engine.evaluate_providers(
            uow, anomaly, impact, self.providers
        )
        
        # 2. Map generic result to ORM
        # Using ContributingFactorAnalysis alias to interact with fuel_root_cause_analyses table
        analysis = ContributingFactorAnalysis(
            anomaly_reference=analysis_result.anomaly_reference,
            financial_impact_reference=analysis_result.financial_impact_reference,
            entity_id=analysis_result.entity_id,
            entity_type=analysis_result.entity_type,
            period_start=analysis_result.period_start,
            period_end=analysis_result.period_end
        )
        
        db_evidence_items = []
        for i, er in enumerate(analysis_result.contributing_factors):
            ev = ContributingFactorEvidence(
                cause_type=er.factor_type,
                evidence_status=er.evidence_status,
                evidence_strength=er.evidence_strength,
                evidence_value=er.evidence_value,
                baseline_value=er.baseline_value,
                deviation_percent=er.deviation_percent,
                unit=er.unit,
                explanation=er.explanation,
                source_references=er.source_references,
                rank=i+1
            )
            db_evidence_items.append(ev)
            
        analysis.evidence_items = db_evidence_items
        
        # Upsert using existing repository to avoid touching transaction scopes
        await uow.repositories.fuel_root_cause.upsert_analysis(analysis)
        
        from infrastructure.intelligence.fuel_domain.root_cause.schemas import RootCauseAnalysisResult, RootCauseEvidenceResult
        
        legacy_causes = [
            RootCauseEvidenceResult(
                cause_type=er.factor_type,
                evidence_status=er.evidence_status,
                evidence_strength=er.evidence_strength,
                explanation=er.explanation,
                evidence_value=er.evidence_value,
                baseline_value=er.baseline_value,
                deviation_percent=er.deviation_percent,
                unit=er.unit,
                source_references=er.source_references
            ) for er in analysis_result.contributing_factors
        ]
        
        # Maintain backward compatibility by returning the legacy typed result
        return RootCauseAnalysisResult(
            status="SUCCESS",
            entity_id=analysis_result.entity_id,
            entity_type=analysis_result.entity_type,
            anomaly_reference=analysis_result.anomaly_reference,
            financial_impact_reference=analysis_result.financial_impact_reference,
            period_start=analysis_result.period_start,
            period_end=analysis_result.period_end,
            candidate_causes=legacy_causes
        )
