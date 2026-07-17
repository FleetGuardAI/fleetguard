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

    async def publish_pending(self) -> int:
        """
        Polls for a batch of pending events and publishes them.
        Returns the number of events processed.
        """
        published_count = 0
        
        try:
            async with SqlAlchemyUnitOfWork(self.db_session_factory) as uow:
                # 1. Fetch pending batch
                events = await uow.repositories.outbox.get_pending_batch(batch_size=settings.OUTBOX_BATCH_SIZE)
                
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
                    # We can use the cached object, but we need to merge or just update it via repository
                    # To be clean, let's execute raw update or just merge
                    current_event = await uow.session.merge(event)
                    
                    # Attempt Kafka publish
                    await self.event_bus.publish(current_event.topic, current_event.payload)
                    
                    # Mark successful
                    await uow.repositories.outbox.mark_published(current_event)
                    await uow.commit()
                    published_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to publish outbox event {event.id}: {e}")
                    # Rollback the failed attempt just in case
                    await uow.rollback()
                    
                    # Record the transient failure
                    async with SqlAlchemyUnitOfWork(self.db_session_factory) as failure_uow:
                        failure_event = await failure_uow.session.merge(event)
                        await failure_uow.repositories.outbox.mark_failed(failure_event, str(e))
                        await failure_uow.commit()

        return published_count
