from sqlalchemy import select
from infrastructure.uow import AbstractUnitOfWork
from models.fuel_anomaly import FuelAnomaly
from models.fuel_financial_impact import FuelFinancialImpact
from models.fuel_root_cause import RootCauseType, EvidenceStatus, EvidenceStrength
from infrastructure.intelligence.core.contributing_factors import EvidenceResult
from infrastructure.intelligence.core.provider import BaseContributingFactorProvider

class ExcessDistanceEvidenceProvider(BaseContributingFactorProvider):
    async def evaluate(
        self,
        uow: AbstractUnitOfWork,
        anomaly: FuelAnomaly,
        impact: FuelFinancialImpact | None
    ) -> EvidenceResult:
        
        from models.vehicle_domain import Vehicle
        from models.trip_domain import Trip
        
        veh_stmt = select(Vehicle).where(Vehicle.registration_number == anomaly.entity_id)
        veh = (await uow.db.execute(veh_stmt)).scalar_one_or_none()
        
        if not veh:
            return EvidenceResult(
                factor_type=RootCauseType.EXCESS_DISTANCE,
                evidence_status=EvidenceStatus.UNAVAILABLE,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="Vehicle mapping unavailable for distance check."
            )
            
        trip_stmt = select(Trip).where(
            Trip.vehicle_id == veh.id,
            Trip.actual_start_time <= anomaly.period_end,
            Trip.actual_end_time >= anomaly.period_start,
            Trip.planned_distance != None,
            Trip.actual_distance != None
        )
        trips = (await uow.db.execute(trip_stmt)).scalars().all()
        
        if not trips:
            return EvidenceResult(
                factor_type=RootCauseType.EXCESS_DISTANCE,
                evidence_status=EvidenceStatus.NEUTRAL,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="No completed trips with planned and actual distance found in this period."
            )
            
        total_planned = sum(t.planned_distance for t in trips if t.planned_distance)
        total_actual = sum(t.actual_distance for t in trips if t.actual_distance)
        
        if total_planned <= 0:
            return EvidenceResult(
                factor_type=RootCauseType.EXCESS_DISTANCE,
                evidence_status=EvidenceStatus.UNAVAILABLE,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="Valid planned distance is missing."
            )
            
        excess_dist = total_actual - total_planned
        excess_pct = (excess_dist / total_planned) * 100
        
        trip_refs = ",".join([t.trip_id for t in trips])
        
        if excess_dist > 0 and excess_pct > 10.0:
            return EvidenceResult(
                factor_type=RootCauseType.EXCESS_DISTANCE,
                evidence_status=EvidenceStatus.SUPPORTING,
                evidence_strength=EvidenceStrength.MODERATE_SUPPORT,
                evidence_value=excess_dist,
                baseline_value=total_planned,
                deviation_percent=excess_pct,
                unit="KM",
                source_references=trip_refs,
                explanation=f"Actual distance driven exceeded planned trip distance by {excess_dist:.1f} KM ({excess_pct:.1f}%)."
            )
            
        return EvidenceResult(
            factor_type=RootCauseType.EXCESS_DISTANCE,
            evidence_status=EvidenceStatus.NEUTRAL,
            evidence_strength=EvidenceStrength.NO_EVIDENCE,
            evidence_value=excess_dist,
            baseline_value=total_planned,
            deviation_percent=excess_pct,
            unit="KM",
            source_references=trip_refs,
            explanation=f"No significant excess distance found. Deviated by {excess_dist:.1f} KM ({excess_pct:.1f}%)."
        )
