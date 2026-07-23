"""
FleetGuard — Outbox Worker
A background asyncio task that periodically triggers the OutboxPublisher.
"""

import asyncio
import logging

from config import settings
from infrastructure.events.outbox_publisher import OutboxPublisher

logger = logging.getLogger("fleetguard.infrastructure.events.outbox_worker")


class OutboxWorkerRunner:
    """
    Background worker that continually polls the Outbox.
    """
    def __init__(self, publisher: OutboxPublisher):
        self.publisher = publisher
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """Starts the background polling loop."""
        if self._task is not None:
            return
            
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"OutboxWorker started. Polling every {settings.OUTBOX_POLL_INTERVAL_MS}ms.")

    async def stop(self) -> None:
        """Stops the background polling loop gracefully."""
        if self._task is None:
            return
            
        logger.info("OutboxWorker stopping...")
        self._stop_event.set()
        
        try:
            await asyncio.wait_for(self._task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("OutboxWorker did not shut down gracefully. Forcing cancellation.")
            self._task.cancel()
            
        self._task = None
        logger.info("OutboxWorker stopped.")

    async def _run_loop(self) -> None:
        interval_seconds = settings.OUTBOX_POLL_INTERVAL_MS / 1000.0
        
        while not self._stop_event.is_set():
            try:
                processed = await self.publisher.publish_pending()
                if processed > 0:
                    logger.debug(f"OutboxWorker published {processed} events.")
            except Exception as e:
                logger.error(f"OutboxWorker encountered an unexpected error: {e}")
                
            # Sleep until next poll, checking for stop_event periodically to allow fast shutdown
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                # Normal timeout, continue loop
                pass
