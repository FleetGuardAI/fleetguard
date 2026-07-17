"""
FleetGuard — Maintenance Service
Domain service orchestrating business rules for Maintenance Management.
"""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork
from datetime import datetime

from models.operational_event import OperationalEvent, EventType, EntityType
from models.maintenance_domain import (
    MaintenanceRecord, 
    MaintenanceTask, 
    MaintenanceStatus,
    MaintenanceCategory,
    TaskType,
    TaskStatus
)
from repositories.maintenance_repository import MaintenanceRepository


class MaintenanceService:
    """
    Coordinates Maintenance Domain business rules.
    Receives Canonical Events or handles read-only queries from the API.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for state mutation in the Maintenance Domain.
        Reads a verified OperationalEvent and applies business rules.
        """
        if event.entity_type != EntityType.MAINTENANCE:
            return

        payload = event.payload or {}
        business_id = event.entity_id

        if event.event_type == EventType.MAINTENANCE_CREATED:
            await self._record_maintenance_created(business_id, payload, str(event.id))
        elif event.event_type == EventType.MAINTENANCE_SCHEDULED:
            await self._record_maintenance_scheduled(business_id, payload, str(event.id))
        elif event.event_type == EventType.MAINTENANCE_STARTED:
            await self._record_maintenance_started(business_id, payload, str(event.id))
        elif event.event_type == EventType.MAINTENANCE_COMPLETED:
            await self._record_maintenance_completed(business_id, payload, str(event.id))
        elif event.event_type == EventType.MAINTENANCE_CANCELLED:
            await self._record_maintenance_cancelled(business_id, payload, str(event.id))
        elif event.event_type == EventType.MAINTENANCE_TASK_ADDED:
            await self._record_maintenance_task_added(business_id, payload, str(event.id))
        elif event.event_type == EventType.MAINTENANCE_TASK_COMPLETED:
            await self._record_maintenance_task_completed(business_id, payload, str(event.id))

    async def _record_maintenance_created(self, business_id: str, payload: dict, origin_id: str) -> None:
        record = await self.uow.repositories.maintenance.get_maintenance_by_business_id(business_id)
        if not record:
            record = MaintenanceRecord(
                business_id=business_id,
                status=MaintenanceStatus.CREATED,
                origin_type="verified_event",
                origin_id=origin_id
            )
            
        if "category" in payload:
            try:
                record.category = MaintenanceCategory(payload["category"])
            except ValueError:
                pass
                
        if "vehicle_id" in payload:
            record.vehicle_id = payload["vehicle_id"]
        if "workshop" in payload:
            record.workshop = payload["workshop"]
        if "service_provider" in payload:
            record.service_provider = payload["service_provider"]

        await self.uow.repositories.maintenance.upsert_maintenance_record(record)
        
    async def _record_maintenance_scheduled(self, business_id: str, payload: dict, origin_id: str) -> None:
        record = await self.uow.repositories.maintenance.get_maintenance_by_business_id(business_id)
        if not record:
            return

        record.status = MaintenanceStatus.SCHEDULED
        record.origin_type = "verified_event"
        record.origin_id = origin_id
        
        if "scheduled_date" in payload:
            try:
                record.scheduled_date = datetime.fromisoformat(payload["scheduled_date"])
            except (ValueError, TypeError):
                pass

        if "workshop" in payload:
            record.workshop = payload["workshop"]
        if "service_provider" in payload:
            record.service_provider = payload["service_provider"]
            
        await self.uow.repositories.maintenance.upsert_maintenance_record(record)

    async def _record_maintenance_started(self, business_id: str, payload: dict, origin_id: str) -> None:
        record = await self.uow.repositories.maintenance.get_maintenance_by_business_id(business_id)
        if not record:
            return
            
        record.status = MaintenanceStatus.STARTED
        record.origin_type = "verified_event"
        record.origin_id = origin_id
        await self.uow.repositories.maintenance.upsert_maintenance_record(record)

    async def _record_maintenance_completed(self, business_id: str, payload: dict, origin_id: str) -> None:
        record = await self.uow.repositories.maintenance.get_maintenance_by_business_id(business_id)
        if not record:
            return

        record.status = MaintenanceStatus.COMPLETED
        record.origin_type = "verified_event"
        record.origin_id = origin_id
        
        if "completed_date" in payload:
            try:
                record.completed_date = datetime.fromisoformat(payload["completed_date"])
            except (ValueError, TypeError):
                pass
                
        await self.uow.repositories.maintenance.upsert_maintenance_record(record)
        
    async def _record_maintenance_cancelled(self, business_id: str, payload: dict, origin_id: str) -> None:
        record = await self.uow.repositories.maintenance.get_maintenance_by_business_id(business_id)
        if not record:
            return

        record.status = MaintenanceStatus.CANCELLED
        record.origin_type = "verified_event"
        record.origin_id = origin_id
        await self.uow.repositories.maintenance.upsert_maintenance_record(record)

    async def _record_maintenance_task_added(self, business_id: str, payload: dict, origin_id: str) -> None:
        record = await self.uow.repositories.maintenance.get_maintenance_by_business_id(business_id)
        if not record:
            return
            
        task = MaintenanceTask(
            maintenance_record_id=record.id,
            description=payload.get("description", "Unknown Task"),
            status=TaskStatus.PENDING,
            notes=payload.get("notes"),
            origin_type="verified_event",
            origin_id=origin_id
        )
        
        if "task_type" in payload:
            try:
                task.task_type = TaskType(payload["task_type"])
            except ValueError:
                task.task_type = TaskType.OTHER
                
        await self.uow.repositories.maintenance.upsert_maintenance_task(task)

    async def _record_maintenance_task_completed(self, business_id: str, payload: dict, origin_id: str) -> None:
        if "task_id" not in payload:
            return
            
        task = await self.uow.repositories.maintenance.get_task_by_id(payload["task_id"])
        if not task:
            return
            
        if "status" in payload:
            try:
                task.status = TaskStatus(payload["status"])
            except ValueError:
                pass
                
        if "performed_at" in payload:
            try:
                task.performed_at = datetime.fromisoformat(payload["performed_at"])
            except (ValueError, TypeError):
                pass
                
        if "notes" in payload:
            task.notes = payload["notes"]
            
        task.origin_type = "verified_event"
        task.origin_id = origin_id
        
        await self.uow.repositories.maintenance.upsert_maintenance_task(task)

    # --- Read APIs ---

    async def get_maintenance(self, maintenance_id: int) -> Optional[MaintenanceRecord]:
        return await self.uow.repositories.maintenance.get_maintenance_by_id(maintenance_id)
        
    async def get_maintenance_by_vehicle(self, vehicle_id: int, limit: int = 50, offset: int = 0) -> Sequence[MaintenanceRecord]:
        return await self.uow.repositories.maintenance.get_maintenance_by_vehicle(vehicle_id, limit, offset)

    async def search_maintenance(
        self, 
        status: Optional[MaintenanceStatus] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[MaintenanceRecord]:
        return await self.uow.repositories.maintenance.search_maintenance(status=status, limit=limit, offset=offset)
