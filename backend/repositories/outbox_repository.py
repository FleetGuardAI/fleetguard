"""
FleetGuard — Outbox Repository
Provides data access to the Outbox events.
"""

from typing import Any, Optional, Sequence
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update
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
        headers: Optional[dict[str, Any]] = None,
        status: OutboxStatus = OutboxStatus.PENDING
    ) -> OutboxEvent:
        """
        Stage an event for publishing inside the current Unit of Work.
        Supports setting initial status (e.g. PUBLISHING for immediate inline claim)
        and records claimed_at timestamp in headers.
        """
        hdrs = dict(headers or {})
        if status == OutboxStatus.PUBLISHING and "claimed_at" not in hdrs:
            hdrs["claimed_at"] = datetime.now(timezone.utc).isoformat()

        event = OutboxEvent(
            event_id=event_id,
            topic=topic,
            payload=payload,
            headers=hdrs if hdrs else None,
            status=status
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_pending_batch(
        self,
        batch_size: int = 50,
        max_retries: int = 5
    ) -> Sequence[OutboxEvent]:
        """
        Load a batch of pending events in deterministic creation order.
        Filters out events that have exceeded max_retries (bounded retry safety).
        Uses FOR UPDATE SKIP LOCKED for safe concurrent worker execution.
        """
        stmt = (
            select(OutboxEvent)
            .where(
                OutboxEvent.status == OutboxStatus.PENDING,
                OutboxEvent.retry_count < max_retries
            )
            .order_by(OutboxEvent.created_at.asc(), OutboxEvent.id.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def recover_stale_publishing(
        self,
        stale_threshold_seconds: int = 30
    ) -> int:
        """
        Recovers events stuck in PUBLISHING status due to an unhandled crash or process restart.
        Evaluates claimed_at in headers (falling back to created_at) to ensure actively
        processing entries are never prematurely reclaimed.
        Resets stale entries to PENDING for automatic re-polling.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_threshold_seconds)
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PUBLISHING)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(stmt)
        publishing_events = result.scalars().all()
        recovered_count = 0
        for ev in publishing_events:
            claimed_at_val = (ev.headers or {}).get("claimed_at")
            if claimed_at_val:
                try:
                    claimed_dt = datetime.fromisoformat(claimed_at_val)
                except (ValueError, TypeError):
                    claimed_dt = ev.created_at
            else:
                claimed_dt = ev.created_at

            if claimed_dt is not None:
                if claimed_dt.tzinfo is None:
                    claimed_dt = claimed_dt.replace(tzinfo=timezone.utc)

                if claimed_dt <= cutoff:
                    ev.status = OutboxStatus.PENDING
                    ev.retry_count += 1
                    ev.last_error = f"Recovered stale PUBLISHING claim after {stale_threshold_seconds}s timeout"
                    recovered_count += 1

        if recovered_count > 0:
            await self.db.flush()
        return recovered_count

    async def mark_publishing(self, events: Sequence[OutboxEvent]) -> None:
        """
        Marks a batch of events as PUBLISHING before attempt.
        Validates state transitions and updates claimed_at lease timestamp in headers.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        for event in events:
            if event.status == OutboxStatus.PUBLISHED:
                raise ValueError(f"Cannot transition terminal PUBLISHED event {event.id} to PUBLISHING")
            event.status = OutboxStatus.PUBLISHING
            event.headers = {**(event.headers or {}), "claimed_at": now_iso}
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
        Rejects invalid transitions from terminal PUBLISHED status.
        """
        if event.status == OutboxStatus.PUBLISHED:
            raise ValueError(f"Cannot transition terminal PUBLISHED event {event.id} to PENDING/failed")
        event.status = OutboxStatus.PENDING  # Reset for retry
        event.retry_count += 1
        event.last_error = error
        await self.db.flush()

    async def get_by_event_id(self, event_id: str) -> Optional[OutboxEvent]:
        """
        Lookup an outbox event by original operational event_id.
        """
        stmt = select(OutboxEvent).where(OutboxEvent.event_id == event_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_dead_letter_events(self, max_retries: int = 5) -> Sequence[OutboxEvent]:
        """
        Selects all outbox events that have exhausted retry limits and remain unfulfilled.
        Provides observability into failed/poison events.
        """
        stmt = (
            select(OutboxEvent)
            .where(
                OutboxEvent.status == OutboxStatus.PENDING,
                OutboxEvent.retry_count >= max_retries
            )
            .order_by(OutboxEvent.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
