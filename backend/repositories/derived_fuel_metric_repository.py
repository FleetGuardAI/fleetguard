"""
FleetGuard — Derived Fuel Metric Repository
Queries historical normalized fuel intelligence observations.
"""

from typing import Sequence, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.derived_fuel_metrics import DerivedFuelMetric, EntityTypeEnum, FuelMetricType

class DerivedFuelMetricRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_historical_observations(
        self,
        entity_id: str,
        entity_type: EntityTypeEnum,
        metric_type: FuelMetricType,
        period_start: datetime,
        period_end: datetime,
    ) -> Sequence[DerivedFuelMetric]:
        """
        Retrieves historical derived fuel metrics for a specific entity and metric type
        within a requested period. This is the primary input source for the Baseline Engine.
        """
        stmt = (
            select(DerivedFuelMetric)
            .where(
                DerivedFuelMetric.entity_id == entity_id,
                DerivedFuelMetric.entity_type == entity_type,
                DerivedFuelMetric.metric_type == metric_type,
                DerivedFuelMetric.period_start >= period_start,
                DerivedFuelMetric.period_end <= period_end
            )
            .order_by(DerivedFuelMetric.period_start.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_source_reference(self, source_reference: str) -> Optional[DerivedFuelMetric]:
        """
        Retrieves a derived fuel metric by its exact source reference.
        Used primarily for idempotency checks.
        """
        stmt = select(DerivedFuelMetric).where(DerivedFuelMetric.source_reference == source_reference)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_metric(self, metric: DerivedFuelMetric) -> DerivedFuelMetric:
        """
        Inserts or updates a derived fuel metric.
        If a metric with the same source_reference already exists, updates it.
        """
        if metric.source_reference:
            existing = await self.get_by_source_reference(metric.source_reference)
            if existing:
                existing.value = metric.value
                existing.quality = metric.quality
                existing.period_start = metric.period_start
                existing.period_end = metric.period_end
                existing.sample_size = metric.sample_size
                self.db.add(existing)
                await self.db.flush()
                await self.db.refresh(existing)
                return existing
        
        self.db.add(metric)
        await self.db.flush()
        await self.db.refresh(metric)
        return metric
