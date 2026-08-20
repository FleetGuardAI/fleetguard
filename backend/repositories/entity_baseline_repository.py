"""
FleetGuard — Entity Baseline Repository
Persists and retrieves successful baseline calculations.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.entity_baseline import EntityBaseline, EntityTypeEnum, FuelMetricType

class EntityBaselineRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_baseline(
        self,
        entity_id: str,
        entity_type: EntityTypeEnum,
        metric_type: FuelMetricType,
        period_start: datetime,
        period_end: datetime,
    ) -> Optional[EntityBaseline]:
        """
        Retrieves a specific baseline by its exact scoping boundaries.
        """
        stmt = select(EntityBaseline).where(
            EntityBaseline.entity_id == entity_id,
            EntityBaseline.entity_type == entity_type,
            EntityBaseline.metric_type == metric_type,
            EntityBaseline.period_start == period_start,
            EntityBaseline.period_end == period_end
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_baseline(self, baseline: EntityBaseline) -> EntityBaseline:
        """
        Inserts a new baseline or updates an existing one if the exact period and entity scope already exists.
        """
        existing = await self.get_baseline(
            entity_id=baseline.entity_id,
            entity_type=baseline.entity_type,
            metric_type=baseline.metric_type,
            period_start=baseline.period_start,
            period_end=baseline.period_end
        )
        
        if existing:
            existing.baseline_value = baseline.baseline_value
            existing.unit = baseline.unit
            existing.sample_size = baseline.sample_size
            existing.calculation_method = baseline.calculation_method
            existing.data_quality = baseline.data_quality
            existing.status = baseline.status
            self.db.add(existing)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            self.db.add(baseline)
            await self.db.flush()
            await self.db.refresh(baseline)
            return baseline
