from infrastructure.uow import AbstractUnitOfWork
from models.fuel_anomaly import FuelAnomaly
from models.fuel_financial_impact import FuelFinancialImpact
from models.fuel_root_cause import RootCauseType, EvidenceStatus, EvidenceStrength
from models.operational_event import EventType, EntityType
from infrastructure.intelligence.core.contributing_factors import EvidenceResult
from infrastructure.intelligence.core.provider import BaseContributingFactorProvider

class FuelEventEvidenceProvider(BaseContributingFactorProvider):
    async def evaluate(
        self,
        uow: AbstractUnitOfWork,
        anomaly: FuelAnomaly,
        impact: FuelFinancialImpact | None
    ) -> EvidenceResult:
        
        # For tests that use mock repository, we can just use list_events_by_entity
        try:
            events = await uow.repositories.operational_event.list_events_by_entity(
                entity_type=EntityType.VEHICLE,
                entity_id=anomaly.entity_id,
                limit=1000
            )
        except AttributeError:
            # Fallback if operational_event is not mocked properly or doesn't exist
            return EvidenceResult(
                factor_type=RootCauseType.FUEL_EVENT_ANOMALY,
                evidence_status=EvidenceStatus.UNAVAILABLE,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="Operational events unavailable."
            )
            
        # Look for FUEL_DRAINED events in the interval
        drain_events = [
            e for e in events 
            if e.event_type == EventType.FUEL_DRAINED 
            and anomaly.period_start <= e.occurred_at <= anomaly.period_end
        ]
        
        if not drain_events:
            return EvidenceResult(
                factor_type=RootCauseType.FUEL_EVENT_ANOMALY,
                evidence_status=EvidenceStatus.NEUTRAL,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="No abnormal fuel events (such as drains) detected during this period."
            )
            
        # Calculate total drained
        total_drained = 0.0
        verified_theft = False
        
        for e in drain_events:
            if e.payload:
                liters = e.payload.get("liters", 0)
                total_drained += float(liters)
                if e.payload.get("verified_unauthorized") is True:
                    verified_theft = True
                    
        event_ids = ",".join([str(e.id) for e in drain_events])
        
        if verified_theft:
            return EvidenceResult(
                factor_type=RootCauseType.FUEL_EVENT_ANOMALY,
                evidence_status=EvidenceStatus.SUPPORTING,
                evidence_strength=EvidenceStrength.STRONG_SUPPORT,
                evidence_value=total_drained,
                unit="LITERS",
                source_references=event_ids,
                explanation=f"Explicitly verified unauthorized fuel drain event detected ({total_drained:.1f} L)."
            )
            
        return EvidenceResult(
            factor_type=RootCauseType.FUEL_EVENT_ANOMALY,
            evidence_status=EvidenceStatus.SUPPORTING,
            evidence_strength=EvidenceStrength.MODERATE_SUPPORT,
            evidence_value=total_drained,
            unit="LITERS",
            source_references=event_ids,
            explanation=f"Fuel drain event detected ({total_drained:.1f} L). The event has not been explicitly classified as unauthorized theft."
        )
