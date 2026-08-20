from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.fuel_root_cause import FuelRootCauseAnalysis, FuelRootCauseEvidence

class FuelRootCauseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_anomaly(self, anomaly_reference: str) -> Optional[FuelRootCauseAnalysis]:
        stmt = select(FuelRootCauseAnalysis).where(FuelRootCauseAnalysis.anomaly_reference == anomaly_reference).options(selectinload(FuelRootCauseAnalysis.evidence_items))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_analyses_by_references(self, anomaly_references: list[str]) -> list[FuelRootCauseAnalysis]:
        stmt = select(FuelRootCauseAnalysis).where(FuelRootCauseAnalysis.anomaly_reference.in_(anomaly_references)).options(selectinload(FuelRootCauseAnalysis.evidence_items))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert_analysis(self, analysis: FuelRootCauseAnalysis) -> FuelRootCauseAnalysis:
        existing = await self.get_by_anomaly(analysis.anomaly_reference)
        
        if existing:
            # Update fields
            existing.financial_impact_reference = analysis.financial_impact_reference
            existing.period_start = analysis.period_start
            existing.period_end = analysis.period_end
            existing.status = analysis.status
            
            # Replace evidence items (delete-orphan will handle removed ones)
            existing.evidence_items = analysis.evidence_items
            
            self.db.add(existing)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            self.db.add(analysis)
            await self.db.flush()
            await self.db.refresh(analysis)
            return analysis
