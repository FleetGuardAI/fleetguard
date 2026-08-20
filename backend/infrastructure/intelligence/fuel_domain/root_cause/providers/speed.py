from sqlalchemy import select
from infrastructure.uow import AbstractUnitOfWork
from models.fuel_anomaly import FuelAnomaly
from models.fuel_financial_impact import FuelFinancialImpact
from models.fuel_root_cause import RootCauseType, EvidenceStatus, EvidenceStrength
from models.location_tracking import LocationAlert, AlertType
from infrastructure.intelligence.core.contributing_factors import EvidenceResult
from infrastructure.intelligence.core.provider import BaseContributingFactorProvider

class SpeedEvidenceProvider(BaseContributingFactorProvider):
    async def evaluate(
        self,
        uow: AbstractUnitOfWork,
        anomaly: FuelAnomaly,
        impact: FuelFinancialImpact | None
    ) -> EvidenceResult:
        
        # Get driver ID from the trips in that period, or just query alerts by company/driver if we had entity mapping.
        # But `LocationAlert` doesn't have vehicle_id, only driver_id.
        # We need trips in that period to find the driver_id(s) for the vehicle.
        from models.vehicle_domain import Vehicle
        from models.trip_domain import Trip
        
        veh_stmt = select(Vehicle).where(Vehicle.registration_number == anomaly.entity_id)
        veh = (await uow.db.execute(veh_stmt)).scalar_one_or_none()
        
        if not veh:
            return EvidenceResult(
                factor_type=RootCauseType.HIGH_SPEED,
                evidence_status=EvidenceStatus.UNAVAILABLE,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="Vehicle mapping unavailable."
            )
            
        trip_stmt = select(Trip).where(
            Trip.vehicle_id == veh.id,
            Trip.actual_start_time <= anomaly.period_end,
            Trip.actual_end_time >= anomaly.period_start,
            Trip.driver_id != None
        )
        trips = (await uow.db.execute(trip_stmt)).scalars().all()
        
        driver_ids = list(set(t.driver_id for t in trips if t.driver_id))
        
        if not driver_ids:
            return EvidenceResult(
                factor_type=RootCauseType.HIGH_SPEED,
                evidence_status=EvidenceStatus.UNAVAILABLE,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="No assigned driver records found for this period."
            )
            
        alert_stmt = select(LocationAlert).where(
            LocationAlert.driver_id.in_(driver_ids),
            LocationAlert.alert_type == AlertType.SPEED_VIOLATION,
            LocationAlert.created_at >= anomaly.period_start,
            LocationAlert.created_at <= anomaly.period_end
        )
        
        alerts = (await uow.db.execute(alert_stmt)).scalars().all()
        
        if not alerts:
            return EvidenceResult(
                factor_type=RootCauseType.HIGH_SPEED,
                evidence_status=EvidenceStatus.NEUTRAL,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="No speed violations recorded during this period."
            )
            
        violation_count = len(alerts)
        alert_ids = ",".join([str(a.id) for a in alerts])
        
        # Determine strength based on count. 1-2 is weak, 3+ is moderate.
        if violation_count >= 3:
            strength = EvidenceStrength.MODERATE_SUPPORT
            desc = "Multiple"
        else:
            strength = EvidenceStrength.WEAK_SUPPORT
            desc = "Occasional"
            
        return EvidenceResult(
            factor_type=RootCauseType.HIGH_SPEED,
            evidence_status=EvidenceStatus.SUPPORTING,
            evidence_strength=strength,
            evidence_value=float(violation_count),
            unit="VIOLATIONS",
            source_references=alert_ids,
            explanation=f"{desc} speed violations ({violation_count}) were recorded during this period. Excessive speed may contribute to degraded fuel efficiency."
        )
