from datetime import datetime
from typing import List, Dict
from sqlalchemy import select

from infrastructure.uow import AbstractUnitOfWork
from models.vehicle_domain import Vehicle
from models.fuel_anomaly import AnomalySeverity, AnomalyStatus
from models.fuel_root_cause import RootCauseType, EvidenceStrength
from infrastructure.intelligence.fuel_domain.financial.summary_schemas import (
    FleetFinancialIntelligenceSummary,
    TruckFinancialIntelligence,
    ContributingFactorSummary
)

class FleetFinancialIntelligenceService:
    async def get_fleet_summary(
        self,
        uow: AbstractUnitOfWork,
        fleet_id: int,
        period_start: datetime,
        period_end: datetime,
        top_n: int = 5
    ) -> FleetFinancialIntelligenceSummary:
        
        # 1. Fetch fleet vehicles
        veh_stmt = select(Vehicle).where(Vehicle.company_id == fleet_id)
        vehicles = (await uow.session.execute(veh_stmt)).scalars().all()
        
        total_trucks = len(vehicles)
        if total_trucks == 0:
            return self._empty_summary(str(fleet_id), period_start, period_end)
            
        vehicle_ids = [v.registration_number for v in vehicles if v.registration_number]
        
        # 2. Fetch financial impacts
        impacts = await uow.repositories.fuel_financial_impact.get_impacts_for_entities(
            vehicle_ids, period_start, period_end
        )
        
        # 3. Fetch anomalies for data quality & severity
        anomalies = await uow.repositories.fuel_anomaly.get_anomalies_for_entities(
            vehicle_ids, period_start, period_end
        )
        anomaly_map = {a.observation_reference: a for a in anomalies}
        
        # Determine insufficient intelligence base
        trucks_with_insufficient_data = len(set(
            a.entity_id for a in anomalies if a.status == AnomalyStatus.INSUFFICIENT_DATA
        ))
        
        # We also need root causes for anomalies that have valid impacts
        valid_impact_refs = [i.anomaly_reference for i in impacts]
        root_causes = await uow.repositories.fuel_root_cause.get_analyses_by_references(valid_impact_refs)
        root_cause_map = {rc.anomaly_reference: rc for rc in root_causes}
        
        # 4. Aggregate by truck
        truck_impacts = {}
        for impact in impacts:
            if impact.entity_id not in truck_impacts:
                truck_impacts[impact.entity_id] = []
            truck_impacts[impact.entity_id].append(impact)
            
        truck_summaries = []
        for truck_id, t_impacts in truck_impacts.items():
            t_impacts.sort(key=lambda i: i.period_start)
            
            data_conflict = False
            for idx in range(1, len(t_impacts)):
                if t_impacts[idx].period_start < t_impacts[idx-1].period_end:
                    data_conflict = True
                    break
                    
            if data_conflict:
                truck_summaries.append(
                    TruckFinancialIntelligence(
                        truck_id=truck_id,
                        estimated_exposure=0.0,
                        excess_fuel_liters=0.0,
                        anomaly_count=len(t_impacts),
                        worst_deviation_percent=0.0,
                        severity=AnomalySeverity.NORMAL,
                        top_contributing_factor=RootCauseType.UNKNOWN,
                        top_contributing_strength=EvidenceStrength.NO_EVIDENCE,
                        period_start=t_impacts[0].period_start,
                        period_end=t_impacts[-1].period_end,
                        data_conflict=True
                    )
                )
                continue
                
            exposure = 0.0
            excess = 0.0
            worst_dev = 0.0
            highest_sev = AnomalySeverity.NORMAL
            top_cause = RootCauseType.UNKNOWN
            top_strength = EvidenceStrength.NO_EVIDENCE
            
            for impact in t_impacts:
                if impact.estimated_financial_exposure:
                    exposure += impact.estimated_financial_exposure
                if impact.excess_fuel_liters:
                    excess += impact.excess_fuel_liters
                    
                anomaly = anomaly_map.get(impact.anomaly_reference)
                if anomaly:
                    # More negative is worse deviation
                    if anomaly.deviation_percent is not None and anomaly.deviation_percent < worst_dev:
                        worst_dev = anomaly.deviation_percent
                        
                    if anomaly.severity == AnomalySeverity.CRITICAL:
                        highest_sev = AnomalySeverity.CRITICAL
                    elif anomaly.severity == AnomalySeverity.WARNING and highest_sev != AnomalySeverity.CRITICAL:
                        highest_sev = AnomalySeverity.WARNING
                        
                rc = root_cause_map.get(impact.anomaly_reference)
                if rc and rc.evidence_items:
                    rc.evidence_items.sort(key=lambda x: x.rank)
                    best_ev = rc.evidence_items[0]
                    # Simple strength rank
                    def s_rank(s):
                        return {EvidenceStrength.STRONG_SUPPORT: 3, EvidenceStrength.MODERATE_SUPPORT: 2, EvidenceStrength.WEAK_SUPPORT: 1}.get(s, 0)
                    
                    if s_rank(best_ev.evidence_strength) > s_rank(top_strength):
                        top_strength = best_ev.evidence_strength
                        top_cause = best_ev.cause_type

            truck_summaries.append(
                TruckFinancialIntelligence(
                    truck_id=truck_id,
                    estimated_exposure=exposure,
                    excess_fuel_liters=excess,
                    anomaly_count=len(t_impacts),
                    worst_deviation_percent=worst_dev,
                    severity=highest_sev,
                    top_contributing_factor=top_cause,
                    top_contributing_strength=top_strength,
                    period_start=t_impacts[0].period_start,
                    period_end=t_impacts[-1].period_end,
                    data_conflict=False
                )
            )
            
        affected_trucks = [ts for ts in truck_summaries if not ts.data_conflict and ts.estimated_exposure > 0]
        
        total_exposure = sum(t.estimated_exposure for t in affected_trucks)
        total_excess = sum(t.excess_fuel_liters for t in affected_trucks)
        
        affected_count = len(affected_trucks)
        avg_exposure = total_exposure / affected_count if affected_count > 0 else 0.0
        
        # Sort for top_exposures
        truck_summaries.sort(key=lambda t: t.estimated_exposure, reverse=True)
        top_exposures = truck_summaries[:top_n]
        
        # Contributing Factor Aggregation
        factors = {}
        for t in affected_trucks:
            if t.top_contributing_factor not in factors:
                factors[t.top_contributing_factor] = {
                    "count": 0,
                    "exposure": 0.0,
                    "strengths": {EvidenceStrength.STRONG_SUPPORT: 0, EvidenceStrength.MODERATE_SUPPORT: 0, EvidenceStrength.WEAK_SUPPORT: 0, EvidenceStrength.NO_EVIDENCE: 0},
                    "highest": EvidenceStrength.NO_EVIDENCE
                }
            f = factors[t.top_contributing_factor]
            f["count"] += 1
            f["exposure"] += t.estimated_exposure
            f["strengths"][t.top_contributing_strength] += 1
            
            def s_rank(s):
                return {EvidenceStrength.STRONG_SUPPORT: 3, EvidenceStrength.MODERATE_SUPPORT: 2, EvidenceStrength.WEAK_SUPPORT: 1}.get(s, 0)
            
            if s_rank(t.top_contributing_strength) > s_rank(f["highest"]):
                f["highest"] = t.top_contributing_strength
                
        factor_summaries = []
        for cause, data in factors.items():
            factor_summaries.append(
                ContributingFactorSummary(
                    cause_type=cause,
                    affected_truck_count=data["count"],
                    total_estimated_exposure=data["exposure"],
                    highest_observed_strength=data["highest"],
                    strength_counts=data["strengths"]
                )
            )
            
        trucks_with_sufficient_intelligence = len(set(
            a.entity_id for a in anomalies if a.status in [AnomalyStatus.ANOMALY, AnomalyStatus.NORMAL]
        ))
        
        # "A truck with sufficient data and no anomaly must NOT be classified as insufficient."
        # If it has sufficient intel but is not in affected_trucks, it's without anomaly
        trucks_without_anomaly = trucks_with_sufficient_intelligence - affected_count
        if trucks_without_anomaly < 0:
            trucks_without_anomaly = 0
            
        return FleetFinancialIntelligenceSummary(
            period_start=period_start,
            period_end=period_end,
            fleet_id=str(fleet_id),
            total_trucks=total_trucks,
            trucks_with_sufficient_intelligence=trucks_with_sufficient_intelligence,
            trucks_with_insufficient_data=trucks_with_insufficient_data,
            affected_trucks=affected_count,
            trucks_without_anomaly=trucks_without_anomaly,
            total_estimated_exposure=total_exposure,
            total_excess_fuel_liters=total_excess,
            average_exposure_per_affected_truck=avg_exposure,
            top_exposures=top_exposures,
            contributing_factor_summary=factor_summaries
        )

    def _empty_summary(self, fleet_id: str, start: datetime, end: datetime) -> FleetFinancialIntelligenceSummary:
        return FleetFinancialIntelligenceSummary(
            period_start=start,
            period_end=end,
            fleet_id=fleet_id,
            total_trucks=0,
            trucks_with_sufficient_intelligence=0,
            trucks_with_insufficient_data=0,
            affected_trucks=0,
            trucks_without_anomaly=0,
            total_estimated_exposure=0.0,
            total_excess_fuel_liters=0.0,
            average_exposure_per_affected_truck=0.0,
            top_exposures=[],
            contributing_factor_summary=[]
        )
