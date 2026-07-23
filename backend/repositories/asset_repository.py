"""
FleetGuard — Asset Repository
Handles database operations for the Asset Domain.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.asset_domain import Asset, AssetHistory, AssetInstallationStatus, AssetOperationalStatus


class AssetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_asset_by_id(self, asset_id: int) -> Optional[Asset]:
        return await self.db.get(Asset, asset_id)

    async def get_asset_by_business_id(self, business_id: str) -> Optional[Asset]:
        stmt = select(Asset).where(Asset.business_id == business_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_assets_by_vehicle(self, vehicle_id: int, limit: int = 50, offset: int = 0) -> Sequence[Asset]:
        stmt = select(Asset).where(Asset.current_vehicle_id == vehicle_id).order_by(Asset.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_assets(
        self, 
        installation_status: Optional[AssetInstallationStatus] = None, 
        operational_status: Optional[AssetOperationalStatus] = None,
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[Asset]:
        query = select(Asset)
        
        if installation_status is not None:
            query = query.where(Asset.installation_status == installation_status)
        if operational_status is not None:
            query = query.where(Asset.operational_status == operational_status)

        query = query.order_by(Asset.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def upsert_asset(self, asset: Asset) -> Asset:
        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset)
        return asset
        
    async def add_history_record(self, record: AssetHistory) -> AssetHistory:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record
