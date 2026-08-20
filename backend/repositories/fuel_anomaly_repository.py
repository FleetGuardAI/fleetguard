"""
FleetGuard — Fuel Anomaly Repository
Persists anomaly detection results.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.fuel_anomaly import FuelAnomaly

class FuelAnomalyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_observation(self, observation_reference: str) -> Optional[FuelAnomaly]:
        """
        Retrieves a fuel anomaly by its unique observation reference.
        """
        stmt = select(FuelAnomaly).where(FuelAnomaly.observation_reference == observation_reference)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_anomalies_for_entities(self, entity_ids: list[str], period_start, period_end) -> list[FuelAnomaly]:
        stmt = select(FuelAnomaly).where(
            FuelAnomaly.entity_id.in_(entity_ids),
            FuelAnomaly.period_start >= period_start,
            FuelAnomaly.period_end <= period_end
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_anomalies_by_references(self, observation_references: list[str]) -> list[FuelAnomaly]:
        """
        Retrieves a list of fuel anomalies by their unique observation references.
        """
        stmt = select(FuelAnomaly).where(FuelAnomaly.observation_reference.in_(observation_references))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert_anomaly(self, anomaly: FuelAnomaly) -> FuelAnomaly:
        """
        Inserts a new anomaly or updates an existing one if the observation already generated an anomaly.
        """
        existing = await self.get_by_observation(anomaly.observation_reference)
        
        if existing:
            existing.baseline_value = anomaly.baseline_value
            existing.observed_value = anomaly.observed_value
            existing.deviation_percent = anomaly.deviation_percent
            existing.direction = anomaly.direction
            existing.severity = anomaly.severity
            existing.status = anomaly.status
            existing.baseline_reference = anomaly.baseline_reference
            existing.period_start = anomaly.period_start
            existing.period_end = anomaly.period_end
            self.db.add(existing)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            self.db.add(anomaly)
            await self.db.flush()
            await self.db.refresh(anomaly)
            return anomaly
