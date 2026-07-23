"""
FleetGuard — Processing Repository
Handles database operations for ProcessingRecord.
"""

from typing import Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models.processing_record import ProcessingRecord, ProcessingStatus


class ProcessingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_record(self, event_id: str, status: ProcessingStatus = ProcessingStatus.PENDING) -> ProcessingRecord:
        record = ProcessingRecord(event_id=event_id, status=status)
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def update_record(
        self, 
        record_id: int, 
        status: ProcessingStatus,
        domains_invoked: Optional[list[str]] = None,
        domains_failed: Optional[list[dict[str, Any]]] = None,
        completed_at: Optional[datetime] = None,
        execution_ms: Optional[int] = None
    ) -> Optional[ProcessingRecord]:
        record = await self.db.get(ProcessingRecord, record_id)
        if not record:
            return None
            
        record.status = status
        
        if domains_invoked is not None:
            record.domains_invoked = domains_invoked
            
        if domains_failed is not None:
            record.domains_failed = domains_failed
            
        if completed_at is not None:
            record.completed_at = completed_at
            
        if execution_ms is not None:
            record.execution_ms = execution_ms
            
        await self.db.flush()
        await self.db.refresh(record)
        return record
