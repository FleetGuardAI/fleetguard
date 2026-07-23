"""
FleetGuard — Tyre Service
Domain service orchestrating business rules for Tyre Management.
"""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork
from datetime import datetime

from models.operational_event import OperationalEvent, EventType, EntityType
from models.tyre_domain import (
    Tyre, 
    TyreLifecycleRecord, 
    TyreStatus,
    LifecycleEventCategory
)
from repositories.tyre_repository import TyreRepository


class TyreService:
    """
    Coordinates Tyre Domain business rules.
    Receives Canonical Events or handles read-only queries from the API.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for state mutation in the Tyre Domain.
        Reads a verified OperationalEvent and applies business rules.
        """
        if event.entity_type != EntityType.TYRE:
            return

        payload = event.payload or {}
        serial_number = event.entity_id

        if event.event_type == EventType.TYRE_REGISTERED:
            await self._record_tyre_registered(serial_number, payload, str(event.id))
        elif event.event_type == EventType.TYRE_INSTALLED:
            await self._record_tyre_installed(serial_number, payload, str(event.id))
        elif event.event_type == EventType.TYRE_REMOVED:
            await self._record_tyre_removed(serial_number, payload, str(event.id))
        elif event.event_type == EventType.TYRE_ROTATED:
            await self._record_tyre_rotated(serial_number, payload, str(event.id))
        elif event.event_type == EventType.TYRE_REPAIRED:
            await self._record_tyre_repaired(serial_number, payload, str(event.id))
        elif event.event_type == EventType.TYRE_RETREADED:
            await self._record_tyre_retreaded(serial_number, payload, str(event.id))
        elif event.event_type == EventType.TYRE_RETIRED:
            await self._record_tyre_retired(serial_number, payload, str(event.id))

    async def _record_tyre_registered(self, serial_number: str, payload: dict, origin_id: str) -> None:
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number(serial_number)
        if not tyre:
            tyre = Tyre(
                serial_number=serial_number,
                current_status=TyreStatus.REGISTERED,
                origin_type="verified_event",
                origin_id=origin_id
            )
            
        tyre.manufacturer = payload.get("manufacturer", tyre.manufacturer)
        tyre.brand = payload.get("brand", tyre.brand)
        tyre.model = payload.get("model", tyre.model)
        tyre.size = payload.get("size", tyre.size)
        tyre.purchase_information = payload.get("purchase_information", tyre.purchase_information)

        await self.uow.repositories.tyre.upsert_tyre(tyre)
        
    async def _record_tyre_installed(self, serial_number: str, payload: dict, origin_id: str) -> None:
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number(serial_number)
        if not tyre:
            return

        tyre.current_status = TyreStatus.INSTALLED
        tyre.current_vehicle_id = payload.get("vehicle_id")
        tyre.current_position = payload.get("position")
        tyre.origin_type = "verified_event"
        tyre.origin_id = origin_id
        await self.uow.repositories.tyre.upsert_tyre(tyre)
        
        await self._append_lifecycle_record(tyre.id, LifecycleEventCategory.INSTALLED, payload, origin_id)

    async def _record_tyre_removed(self, serial_number: str, payload: dict, origin_id: str) -> None:
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number(serial_number)
        if not tyre:
            return
            
        tyre.current_status = TyreStatus.IN_STORAGE
        tyre.current_vehicle_id = None
        tyre.current_position = None
        tyre.origin_type = "verified_event"
        tyre.origin_id = origin_id
        await self.uow.repositories.tyre.upsert_tyre(tyre)
        
        await self._append_lifecycle_record(tyre.id, LifecycleEventCategory.REMOVED, payload, origin_id)

    async def _record_tyre_rotated(self, serial_number: str, payload: dict, origin_id: str) -> None:
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number(serial_number)
        if not tyre:
            return

        if "new_position" in payload:
            tyre.current_position = payload["new_position"]
            tyre.origin_type = "verified_event"
            tyre.origin_id = origin_id
            await self.uow.repositories.tyre.upsert_tyre(tyre)
        
        await self._append_lifecycle_record(tyre.id, LifecycleEventCategory.ROTATED, payload, origin_id)
        
    async def _record_tyre_repaired(self, serial_number: str, payload: dict, origin_id: str) -> None:
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number(serial_number)
        if not tyre:
            return
            
        # Repair might change status if it was IN_REPAIR to IN_STORAGE, 
        # or it might just be an event. We assume the tyre is returned to storage/installed 
        # based on context, but normally it just logs the repair.
        await self._append_lifecycle_record(tyre.id, LifecycleEventCategory.REPAIRED, payload, origin_id)

    async def _record_tyre_retreaded(self, serial_number: str, payload: dict, origin_id: str) -> None:
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number(serial_number)
        if not tyre:
            return
            
        await self._append_lifecycle_record(tyre.id, LifecycleEventCategory.RETREADED, payload, origin_id)

    async def _record_tyre_retired(self, serial_number: str, payload: dict, origin_id: str) -> None:
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number(serial_number)
        if not tyre:
            return
            
        tyre.current_status = TyreStatus.RETIRED
        tyre.current_vehicle_id = None
        tyre.current_position = None
        tyre.origin_type = "verified_event"
        tyre.origin_id = origin_id
        await self.uow.repositories.tyre.upsert_tyre(tyre)
        
        await self._append_lifecycle_record(tyre.id, LifecycleEventCategory.RETIRED, payload, origin_id)

    async def _append_lifecycle_record(self, tyre_id: int, category: LifecycleEventCategory, payload: dict, origin_id: str) -> None:
        performed_at = datetime.utcnow()
        if "performed_at" in payload:
            try:
                performed_at = datetime.fromisoformat(payload["performed_at"])
            except (ValueError, TypeError):
                pass
                
        record = TyreLifecycleRecord(
            tyre_id=tyre_id,
            event_category=category,
            performed_at=performed_at,
            details=payload.get("details"),
            origin_type="verified_event",
            origin_id=origin_id
        )
        await self.uow.repositories.tyre.add_lifecycle_record(record)

    # --- Read APIs ---

    async def get_tyre(self, tyre_id: int) -> Optional[Tyre]:
        return await self.uow.repositories.tyre.get_tyre_by_id(tyre_id)
        
    async def get_tyres_by_vehicle(self, vehicle_id: int, limit: int = 50, offset: int = 0) -> Sequence[Tyre]:
        return await self.uow.repositories.tyre.get_tyres_by_vehicle(vehicle_id, limit, offset)

    async def search_tyres(
        self, 
        status: Optional[TyreStatus] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[Tyre]:
        return await self.uow.repositories.tyre.search_tyres(status=status, limit=limit, offset=offset)
