"""
FleetGuard — Outbox Publisher
Fetches pending outbox events from the database and publishes them to Kafka.
"""

import logging
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from infrastructure.events.bus import EventBus
from infrastructure.uow import SqlAlchemyUnitOfWork

logger = logging.getLogger("fleetguard.infrastructure.events.outbox_publisher")


class OutboxPublisher:
    """
    Responsible for polling the Outbox table and publishing events to Kafka.
    """
    def __init__(self, db_session_factory: Callable[[], AsyncSession], event_bus: EventBus):
        self.db_session_factory = db_session_factory
        self.event_bus = event_bus

    async def recover_stale_claims(self) -> int:
        """
        Recovers any outbox events left in PUBLISHING status due to previous crashes.
        """
        try:
            async with SqlAlchemyUnitOfWork(self.db_session_factory) as uow:
                timeout = getattr(settings, "OUTBOX_STALE_TIMEOUT_SECONDS", 30)
                recovered = await uow.repositories.outbox.recover_stale_publishing(stale_threshold_seconds=timeout)
                if recovered > 0:
                    await uow.commit()
                    logger.warning(f"OutboxPublisher recovered {recovered} stale PUBLISHING events back to PENDING.")
                return recovered
        except Exception as e:
            logger.error(f"Failed to recover stale outbox claims: {e}")
            return 0

    async def publish_pending(self) -> int:
        """
        Polls for a batch of pending events and publishes them.
        Returns the number of events processed.
        """
        published_count = 0
        batch_size = getattr(settings, "OUTBOX_BATCH_SIZE", 50)
        max_retries = getattr(settings, "OUTBOX_MAX_RETRIES", 5)
        
        # 0. Periodically recover any stale PUBLISHING claims
        await self.recover_stale_claims()

        try:
            async with SqlAlchemyUnitOfWork(self.db_session_factory) as uow:
                # 1. Fetch pending batch (bounded by max_retries)
                events = await uow.repositories.outbox.get_pending_batch(
                    batch_size=batch_size,
                    max_retries=max_retries
                )
                
                if not events:
                    return 0
                
                # 2. Mark as PUBLISHING (prevent other workers from grabbing them)
                await uow.repositories.outbox.mark_publishing(events)
                await uow.commit() # Commit the PUBLISHING state
                
        except Exception as e:
            logger.error(f"OutboxPublisher failed to fetch/lock batch: {e}")
            return 0

        # 3. Publish each event
        for event in events:
            # We process each event in its own transaction to ensure one failure doesn't halt the rest
            async with SqlAlchemyUnitOfWork(self.db_session_factory) as uow:
                try:
                    # Re-fetch event inside the loop's transaction
                    current_event = await uow.session.merge(event)
                    
                    # Attempt publish via event bus (in-process or Kafka)
                    await self.event_bus.publish(current_event.topic, current_event.payload)
                    
                    # Mark successful
                    await uow.repositories.outbox.mark_published(current_event)
                    await uow.commit()
                    published_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to publish outbox event {event.id}: {e}")
                    # Rollback the failed attempt just in case
                    await uow.rollback()
                    
                    # Record the failure
                    async with SqlAlchemyUnitOfWork(self.db_session_factory) as failure_uow:
                        failure_event = await failure_uow.session.merge(event)
                        new_retry_count = (failure_event.retry_count or 0) + 1
                        if new_retry_count >= max_retries:
                            err_msg = f"[POISON_PILL / MAX_RETRIES_EXCEEDED] Attempt {new_retry_count}/{max_retries}: {e}"
                            logger.critical(
                                f"Outbox event {event.id} (event_id={event.event_id}) exceeded max retries ({max_retries}). "
                                f"Moved to Dead-Letter state: {e}"
                            )
                        else:
                            err_msg = f"Attempt {new_retry_count}/{max_retries}: {e}"
                        await failure_uow.repositories.outbox.mark_failed(failure_event, err_msg)
                        await failure_uow.commit()

        return published_count
