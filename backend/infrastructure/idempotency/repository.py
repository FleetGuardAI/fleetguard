"""
FleetGuard — Idempotency Repository
Abstracts database queries for the Idempotency Framework.
"""

from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from models.processed_event import ProcessedEvent


class IdempotencyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def has_processed(self, event_id: str, domain_name: str) -> bool:
        """
        Checks if a domain has already processed this event.
        """
        stmt = select(ProcessedEvent).where(
            ProcessedEvent.operational_event_id == event_id,
            ProcessedEvent.domain_name == domain_name
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def mark_processed(
        self, 
        event_id: str, 
        domain_name: str, 
        result: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> ProcessedEvent:
        """
        Records that a domain has successfully processed this event.
        Relies on the caller to commit the transaction.
        Raises IntegrityError if it already exists and caller doesn't check.
        """
        record = ProcessedEvent(
            operational_event_id=event_id,
            domain_name=domain_name,
            processing_result=result,
            metadata_payload=metadata
        )
        self.db.add(record)
        await self.db.flush()
        return record
