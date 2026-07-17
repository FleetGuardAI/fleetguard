"""
FleetGuard — Outbox Repository
Provides data access to the Outbox events.
"""

from typing import Any, Optional, Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.outbox_event import OutboxEvent, OutboxStatus


class OutboxRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(
        self, 
        topic: str, 
        payload: dict[str, Any], 
        event_id: Optional[str] = None,
        headers: Optional[dict[str, Any]] = None
    ) -> OutboxEvent:
        """
        Stage an event for publishing inside the current Unit of Work.
        """
        event = OutboxEvent(
            event_id=event_id,
            topic=topic,
            payload=payload,
            headers=headers,
            status=OutboxStatus.PENDING
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_pending_batch(self, batch_size: int = 50) -> Sequence[OutboxEvent]:
        """
        Load a batch of pending events in deterministic creation order.
        """
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING)
            .order_by(OutboxEvent.created_at.asc(), OutboxEvent.id.asc())
            .limit(batch_size)
            # In a distributed environment with multiple publishers, you might want to use SELECT FOR UPDATE SKIP LOCKED
            # e.g. .with_for_update(skip_locked=True)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def mark_publishing(self, events: Sequence[OutboxEvent]) -> None:
        """
        Marks a batch of events as PUBLISHING before attempt.
        """
        for event in events:
            event.status = OutboxStatus.PUBLISHING
        await self.db.flush()

    async def mark_published(self, event: OutboxEvent) -> None:
        """
        Marks a specific event as successfully published.
        """
        event.status = OutboxStatus.PUBLISHED
        event.published_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def mark_failed(self, event: OutboxEvent, error: str) -> None:
        """
        Records a transient failure for an event, resetting it to PENDING.
        """
        event.status = OutboxStatus.PENDING  # Reset for retry
        event.retry_count += 1
        event.last_error = error
        await self.db.flush()
