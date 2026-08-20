"""
FleetGuard — Fuel Financial Impact Repository
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.fuel_financial_impact import FuelFinancialImpact

class FuelFinancialImpactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_anomaly(self, anomaly_reference: str) -> Optional[FuelFinancialImpact]:
        stmt = select(FuelFinancialImpact).where(FuelFinancialImpact.anomaly_reference == anomaly_reference)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_impacts_for_entities(self, entity_ids: list[str], period_start, period_end) -> list[FuelFinancialImpact]:
        stmt = select(FuelFinancialImpact).where(
            FuelFinancialImpact.entity_id.in_(entity_ids),
            FuelFinancialImpact.period_start >= period_start,
            FuelFinancialImpact.period_end <= period_end
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert_impact(self, impact: FuelFinancialImpact) -> FuelFinancialImpact:
        existing = await self.get_by_anomaly(impact.anomaly_reference)
        
        if existing:
            # New Generic Fields
            existing.baseline_value = impact.baseline_value
            existing.observed_value = impact.observed_value
            existing.domain_context = impact.domain_context
            
            # Legacy Fields (Retained for phased migration dual-write)
            existing.baseline_efficiency = impact.baseline_efficiency
            existing.observed_efficiency = impact.observed_efficiency
            existing.distance = impact.distance
            existing.expected_fuel_liters = impact.expected_fuel_liters
            existing.implied_fuel_liters = impact.implied_fuel_liters
            existing.excess_fuel_liters = impact.excess_fuel_liters
            existing.fuel_price_per_liter = impact.fuel_price_per_liter
            existing.fuel_price_source = impact.fuel_price_source
            
            # Universal Fields
            existing.estimated_financial_exposure = impact.estimated_financial_exposure
            existing.baseline_reference = impact.baseline_reference
            existing.observation_reference = impact.observation_reference
            existing.period_start = impact.period_start
            existing.period_end = impact.period_end
            existing.calculation_method = impact.calculation_method
            
            self.db.add(existing)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            self.db.add(impact)
            await self.db.flush()
            await self.db.refresh(impact)
            return impact
