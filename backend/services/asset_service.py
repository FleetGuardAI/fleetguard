"""
FleetGuard — Asset Service
Domain service orchestrating business rules for Asset Management.
"""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork
from datetime import datetime

from models.operational_event import OperationalEvent, EventType, EntityType
from models.asset_domain import (
    Asset, 
    AssetHistory, 
    AssetType,
    AssetInstallationStatus,
    AssetOperationalStatus,
    AssetHistoryCategory
)
from repositories.asset_repository import AssetRepository


class AssetService:
    """
    Coordinates Asset Domain business rules.
    Receives Canonical Events or handles read-only queries from the API.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for state mutation in the Asset Domain.
        Reads a verified OperationalEvent and applies business rules.
        """
        if event.entity_type != EntityType.ASSET:
            return

        payload = event.payload or {}
        business_id = event.entity_id

        if event.event_type == EventType.ASSET_REGISTERED:
            await self._record_asset_registered(business_id, payload, str(event.id))
        elif event.event_type == EventType.ASSET_INSTALLED:
            await self._record_asset_installed(business_id, payload, str(event.id))
        elif event.event_type == EventType.ASSET_REMOVED:
            await self._record_asset_removed(business_id, payload, str(event.id))
        elif event.event_type == EventType.ASSET_CALIBRATED:
            await self._record_asset_calibrated(business_id, payload, str(event.id))
        elif event.event_type == EventType.ASSET_REPAIRED:
            await self._record_asset_repaired(business_id, payload, str(event.id))
        elif event.event_type == EventType.ASSET_REPLACED:
            await self._record_asset_replaced(business_id, payload, str(event.id))
        elif event.event_type == EventType.ASSET_RETIRED:
            await self._record_asset_retired(business_id, payload, str(event.id))

    async def _record_asset_registered(self, business_id: str, payload: dict, origin_id: str) -> None:
        asset = await self.uow.repositories.asset.get_asset_by_business_id(business_id)
        
        asset_type_str = payload.get("asset_type", "OTHER")
        try:
            asset_type = AssetType(asset_type_str)
        except ValueError:
            asset_type = AssetType.OTHER
            
        if not asset:
            asset = Asset(
                business_id=business_id,
                asset_type=asset_type,
                installation_status=AssetInstallationStatus.REGISTERED,
                operational_status=AssetOperationalStatus.OK,
                origin_type="verified_event",
                origin_id=origin_id
            )
            
        asset.manufacturer = payload.get("manufacturer", asset.manufacturer)
        asset.model = payload.get("model", asset.model)
        asset.serial_number = payload.get("serial_number", asset.serial_number)
        asset.firmware_version = payload.get("firmware_version", asset.firmware_version)
        asset.purchase_information = payload.get("purchase_information", asset.purchase_information)
        asset.warranty_information = payload.get("warranty_information", asset.warranty_information)

        await self.uow.repositories.asset.upsert_asset(asset)
        
    async def _record_asset_installed(self, business_id: str, payload: dict, origin_id: str) -> None:
        asset = await self.uow.repositories.asset.get_asset_by_business_id(business_id)
        if not asset:
            return

        asset.installation_status = AssetInstallationStatus.INSTALLED
        asset.current_vehicle_id = payload.get("vehicle_id")
        asset.origin_type = "verified_event"
        asset.origin_id = origin_id
        await self.uow.repositories.asset.upsert_asset(asset)
        
        await self._append_history_record(asset.id, AssetHistoryCategory.INSTALLED, payload, origin_id)

    async def _record_asset_removed(self, business_id: str, payload: dict, origin_id: str) -> None:
        asset = await self.uow.repositories.asset.get_asset_by_business_id(business_id)
        if not asset:
            return
            
        asset.installation_status = AssetInstallationStatus.IN_STORAGE
        asset.current_vehicle_id = None
        asset.origin_type = "verified_event"
        asset.origin_id = origin_id
        await self.uow.repositories.asset.upsert_asset(asset)
        
        await self._append_history_record(asset.id, AssetHistoryCategory.REMOVED, payload, origin_id)

    async def _record_asset_calibrated(self, business_id: str, payload: dict, origin_id: str) -> None:
        asset = await self.uow.repositories.asset.get_asset_by_business_id(business_id)
        if not asset:
            return
            
        if "firmware_version" in payload:
            asset.firmware_version = payload["firmware_version"]
            await self.uow.repositories.asset.upsert_asset(asset)

        await self._append_history_record(asset.id, AssetHistoryCategory.CALIBRATED, payload, origin_id)
        
    async def _record_asset_repaired(self, business_id: str, payload: dict, origin_id: str) -> None:
        asset = await self.uow.repositories.asset.get_asset_by_business_id(business_id)
        if not asset:
            return
            
        await self._append_history_record(asset.id, AssetHistoryCategory.REPAIRED, payload, origin_id)

    async def _record_asset_replaced(self, business_id: str, payload: dict, origin_id: str) -> None:
        asset = await self.uow.repositories.asset.get_asset_by_business_id(business_id)
        if not asset:
            return
            
        await self._append_history_record(asset.id, AssetHistoryCategory.REPLACED, payload, origin_id)

    async def _record_asset_retired(self, business_id: str, payload: dict, origin_id: str) -> None:
        asset = await self.uow.repositories.asset.get_asset_by_business_id(business_id)
        if not asset:
            return
            
        asset.installation_status = AssetInstallationStatus.RETIRED
        asset.current_vehicle_id = None
        asset.origin_type = "verified_event"
        asset.origin_id = origin_id
        await self.uow.repositories.asset.upsert_asset(asset)
        
        await self._append_history_record(asset.id, AssetHistoryCategory.RETIRED, payload, origin_id)

    async def _append_history_record(self, asset_id: int, category: AssetHistoryCategory, payload: dict, origin_id: str) -> None:
        performed_at = datetime.utcnow()
        if "performed_at" in payload:
            try:
                performed_at = datetime.fromisoformat(payload["performed_at"])
            except (ValueError, TypeError):
                pass
                
        record = AssetHistory(
            asset_id=asset_id,
            event_category=category,
            performed_at=performed_at,
            details=payload.get("details"),
            origin_type="verified_event",
            origin_id=origin_id
        )
        await self.uow.repositories.asset.add_history_record(record)

    # --- Read APIs ---

    async def get_asset(self, asset_id: int) -> Optional[Asset]:
        return await self.uow.repositories.asset.get_asset_by_id(asset_id)
        
    async def get_assets_by_vehicle(self, vehicle_id: int, limit: int = 50, offset: int = 0) -> Sequence[Asset]:
        return await self.uow.repositories.asset.get_assets_by_vehicle(vehicle_id, limit, offset)

    async def search_assets(
        self, 
        installation_status: Optional[AssetInstallationStatus] = None, 
        operational_status: Optional[AssetOperationalStatus] = None,
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[Asset]:
        return await self.uow.repositories.asset.search_assets(
            installation_status=installation_status, 
            operational_status=operational_status, 
            limit=limit, 
            offset=offset
        )
