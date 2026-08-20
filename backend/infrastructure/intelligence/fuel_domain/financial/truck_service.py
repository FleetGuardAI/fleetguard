from datetime import datetime
from typing import List

from infrastructure.uow import AbstractUnitOfWork
from models.vehicle_domain import Vehicle
from infrastructure.intelligence.fuel_domain.financial.truck_schemas import (
    TruckIntelligenceDetailResponse,
    FuelAnomalyResponse,
    FuelFinancialImpactResponse,
    ContributingFactorDetail,
    EvidenceItemResponse
)
from infrastructure.intelligence.fuel_domain.financial.summary_service import FleetFinancialIntelligenceService

class TruckFinancialIntelligenceService:
    async def get_truck_detail(
        self,
        uow: AbstractUnitOfWork,
        truck_id: str,
        company_id: int,
        period_start: datetime,
        period_end: datetime,
        limit: int = 50,
        offset: int = 0
    ) -> TruckIntelligenceDetailResponse:
        
        # 1. Fetch the truck after ownership validation
        veh_repo = uow.repositories.vehicle
        from sqlalchemy import select
        stmt = select(Vehicle).where(Vehicle.registration_number == truck_id, Vehicle.company_id == company_id)
        result = await uow.db.execute(stmt)
        vehicle = result.scalar_one_or_none()
        
        if not vehicle:
            return None # Router will return 404
            
        # 2. Fetch paginated anomalies for the requested period
        # We need to add pagination to the repository method or just filter it here
        from models.fuel_anomaly import FuelAnomaly
        stmt = select(FuelAnomaly).where(
            FuelAnomaly.entity_id == truck_id,
            FuelAnomaly.period_start >= period_start,
            FuelAnomaly.period_end <= period_end
        ).order_by(FuelAnomaly.period_start.desc()).limit(limit).offset(offset)
        
        anomalies = (await uow.db.execute(stmt)).scalars().all()
        
        anomaly_responses = []
        for a in anomalies:
            anomaly_responses.append(
                FuelAnomalyResponse(
                    anomaly_reference=a.observation_reference,
                    observed_value=a.observed_value,
                    baseline_value=a.baseline_value,
                    deviation_percent=a.deviation_percent,
                    direction=a.direction,
                    severity=a.severity,
                    period_start=a.period_start,
                    period_end=a.period_end
                )
            )
            
        # 3. Collect anomaly references
        anomaly_refs = [a.observation_reference for a in anomalies]
        
        # 4. Batch fetch corresponding financial impacts
        impacts = await uow.repositories.fuel_financial_impact.get_impacts_for_entities([truck_id], period_start, period_end)
        # Filter strictly to the paginated anomaly refs
        impacts = [i for i in impacts if i.anomaly_reference in anomaly_refs]
        
        impact_responses = []
        for i in impacts:
            impact_responses.append(
                FuelFinancialImpactResponse(
                    anomaly_reference=i.anomaly_reference,
                    estimated_financial_exposure=i.estimated_financial_exposure,
                    excess_fuel_liters=i.excess_fuel_liters,
                    fuel_price_per_liter=i.fuel_price_per_liter,
                    fuel_price_source=i.fuel_price_source,
                    period_start=i.period_start,
                    period_end=i.period_end
                )
            )
            
        # 5. Batch fetch corresponding root-cause analyses/evidence
        analyses = await uow.repositories.fuel_root_cause.get_analyses_by_references(anomaly_refs)
        
        factor_details = []
        for rc in analyses:
            items = []
            if rc.evidence_items:
                for ev in rc.evidence_items:
                    items.append(
                        EvidenceItemResponse(
                            cause_type=ev.cause_type,
                            evidence_status=ev.evidence_status.value if ev.evidence_status else "UNKNOWN",
                            evidence_strength=ev.evidence_strength,
                            explanation=ev.explanation,
                            source_references=ev.source_references if ev.source_references else []
                        )
                    )
            
            factor_details.append(
                ContributingFactorDetail(
                    anomaly_reference=rc.anomaly_reference,
                    possible_contributing_factors=items
                )
            )
            
        # 6. Construct summary - We must use the exact logic of the fleet summary for this truck 
        # so that it perfectly matches. We will invoke get_fleet_summary but isolate it to this truck?
        # The prompt explicitly forbids: "DO NOT implement truck detail by calling: FleetFinancialIntelligenceService.get_fleet_summary(...) and then filtering the resulting fleet summary."
        # It says "The truck detail service must consume persisted: FuelAnomaly, FuelFinancialImpact... It must not recalculate".
        # We will compute the summary for this single truck using the fetched impacts and anomalies. 
        # But wait, the summary needs to reflect the WHOLE period, not just the paginated slice.
        
        # Fetch ALL impacts for the whole period for the summary
        all_impacts = await uow.repositories.fuel_financial_impact.get_impacts_for_entities([truck_id], period_start, period_end)
        all_impacts.sort(key=lambda x: x.period_start)
        
        all_anomalies = await uow.repositories.fuel_anomaly.get_anomalies_for_entities([truck_id], period_start, period_end)
        all_anomaly_map = {a.observation_reference: a for a in all_anomalies}
        
        all_impact_refs = [i.anomaly_reference for i in all_impacts]
        all_root_causes = await uow.repositories.fuel_root_cause.get_analyses_by_references(all_impact_refs)
        all_root_cause_map = {rc.anomaly_reference: rc for rc in all_root_causes}
        
        data_conflict = False
        for idx in range(1, len(all_impacts)):
            if all_impacts[idx].period_start < all_impacts[idx-1].period_end:
                data_conflict = True
                break
                
        from infrastructure.intelligence.fuel_domain.financial.summary_schemas import TruckFinancialIntelligence
        from models.fuel_anomaly import AnomalySeverity
        from models.fuel_root_cause import RootCauseType, EvidenceStrength
        
        if data_conflict or not all_impacts:
            summary = TruckFinancialIntelligence(
                truck_id=truck_id,
                estimated_exposure=0.0,
                excess_fuel_liters=0.0,
                anomaly_count=len(all_impacts),
                worst_deviation_percent=0.0,
                severity=AnomalySeverity.NORMAL,
                top_contributing_factor=RootCauseType.UNKNOWN,
                top_contributing_strength=EvidenceStrength.NO_EVIDENCE,
                period_start=period_start,
                period_end=period_end,
                data_conflict=data_conflict
            )
        else:
            exposure = sum(i.estimated_financial_exposure or 0.0 for i in all_impacts)
            excess = sum(i.excess_fuel_liters or 0.0 for i in all_impacts)
            worst_dev = 0.0
            highest_sev = AnomalySeverity.NORMAL
            top_cause = RootCauseType.UNKNOWN
            top_strength = EvidenceStrength.NO_EVIDENCE
            
            for impact in all_impacts:
                anomaly = all_anomaly_map.get(impact.anomaly_reference)
                if anomaly:
                    if anomaly.deviation_percent is not None and anomaly.deviation_percent < worst_dev:
                        worst_dev = anomaly.deviation_percent
                    if anomaly.severity == AnomalySeverity.CRITICAL:
                        highest_sev = AnomalySeverity.CRITICAL
                    elif anomaly.severity == AnomalySeverity.WARNING and highest_sev != AnomalySeverity.CRITICAL:
                        highest_sev = AnomalySeverity.WARNING
                        
                rc = all_root_cause_map.get(impact.anomaly_reference)
                if rc and rc.evidence_items:
                    rc.evidence_items.sort(key=lambda x: x.rank)
                    best_ev = rc.evidence_items[0]
                    def s_rank(s):
                        return {EvidenceStrength.STRONG_SUPPORT: 3, EvidenceStrength.MODERATE_SUPPORT: 2, EvidenceStrength.WEAK_SUPPORT: 1}.get(s, 0)
                    
                    if s_rank(best_ev.evidence_strength) > s_rank(top_strength):
                        top_strength = best_ev.evidence_strength
                        top_cause = best_ev.cause_type

            summary = TruckFinancialIntelligence(
                truck_id=truck_id,
                estimated_exposure=exposure,
                excess_fuel_liters=excess,
                anomaly_count=len(all_impacts),
                worst_deviation_percent=worst_dev,
                severity=highest_sev,
                top_contributing_factor=top_cause,
                top_contributing_strength=top_strength,
                period_start=all_impacts[0].period_start,
                period_end=all_impacts[-1].period_end,
                data_conflict=False
            )
            
        return TruckIntelligenceDetailResponse(
            summary=summary,
            anomalies=anomaly_responses,
            financial_impacts=impact_responses,
            contributing_factors=factor_details
        )
