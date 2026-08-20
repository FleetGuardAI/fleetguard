from sqlalchemy import select
from infrastructure.uow import AbstractUnitOfWork
from models.fuel_anomaly import FuelAnomaly
from models.fuel_financial_impact import FuelFinancialImpact
from models.fuel_root_cause import RootCauseType, EvidenceStatus, EvidenceStrength
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus
from infrastructure.intelligence.core.contributing_factors import EvidenceResult
from infrastructure.intelligence.core.provider import BaseContributingFactorProvider

class MaintenanceEvidenceProvider(BaseContributingFactorProvider):
    async def evaluate(
        self,
        uow: AbstractUnitOfWork,
        anomaly: FuelAnomaly,
        impact: FuelFinancialImpact | None
    ) -> EvidenceResult:
        
        from models.vehicle_domain import Vehicle
        
        veh_stmt = select(Vehicle).where(Vehicle.registration_number == anomaly.entity_id)
        veh = (await uow.db.execute(veh_stmt)).scalar_one_or_none()
        
        if not veh:
            return EvidenceResult(
                factor_type=RootCauseType.VEHICLE_MAINTENANCE,
                evidence_status=EvidenceStatus.UNAVAILABLE,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="Vehicle mapping unavailable."
            )
            
        # Look for maintenance records that were overdue during the anomaly period
        maint_stmt = select(MaintenanceRecord).where(
            MaintenanceRecord.vehicle_id == veh.id,
            MaintenanceRecord.status != MaintenanceStatus.COMPLETED,
            MaintenanceRecord.status != MaintenanceStatus.CANCELLED,
            MaintenanceRecord.scheduled_date < anomaly.period_end
        )
        
        records = (await uow.db.execute(maint_stmt)).scalars().all()
        
        if not records:
            return EvidenceResult(
                factor_type=RootCauseType.VEHICLE_MAINTENANCE,
                evidence_status=EvidenceStatus.NEUTRAL,
                evidence_strength=EvidenceStrength.NO_EVIDENCE,
                explanation="No overdue maintenance records found for this period."
            )
            
        record_count = len(records)
        record_ids = ",".join([str(r.id) for r in records])
        
        # Determine strength based on count. 1 is weak, 2+ is moderate.
        if record_count >= 2:
            strength = EvidenceStrength.MODERATE_SUPPORT
            desc = "Multiple overdue maintenance items"
        else:
            strength = EvidenceStrength.WEAK_SUPPORT
            desc = "An overdue maintenance item"
            
        return EvidenceResult(
            factor_type=RootCauseType.VEHICLE_MAINTENANCE,
            evidence_status=EvidenceStatus.SUPPORTING,
            evidence_strength=strength,
            evidence_value=float(record_count),
            unit="RECORDS",
            source_references=record_ids,
            explanation=f"{desc} ({record_count}) observed during this period, potentially degrading vehicle efficiency."
        )
