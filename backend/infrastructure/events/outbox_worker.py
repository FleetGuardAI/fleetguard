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
        self._stop_event: asyncio.Event | None = None

    async def start(self) -> None:
        """Starts the background polling loop bound to the active event loop."""
        if self._task is not None:
            return
            
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run_loop())
        poll_ms = getattr(settings, "OUTBOX_POLL_INTERVAL_MS", 1000)
        logger.info(f"OutboxWorker started. Polling every {poll_ms}ms.")

    async def stop(self) -> None:
        """Stops the background polling loop gracefully."""
        if self._task is None:
            return
            
        logger.info("OutboxWorker stopping...")
        if self._stop_event is not None:
            self._stop_event.set()
        
        try:
            await asyncio.wait_for(self._task, timeout=5.0)
        except (asyncio.TimeoutError, RuntimeError):
            logger.warning("OutboxWorker did not shut down gracefully. Forcing cancellation.")
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        except asyncio.CancelledError:
            pass
            
        self._task = None
        self._stop_event = None
        logger.info("OutboxWorker stopped.")

    async def _run_loop(self) -> None:
        interval_seconds = getattr(settings, "OUTBOX_POLL_INTERVAL_MS", 1000) / 1000.0
        
        while self._stop_event is not None and not self._stop_event.is_set():
            try:
                processed = await self.publisher.publish_pending()
                if processed > 0:
                    logger.debug(f"OutboxWorker published {processed} events.")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"OutboxWorker encountered an unexpected error: {e}")
                
            # Sleep until next poll, checking for stop_event periodically to allow fast shutdown
            if self._stop_event is None or self._stop_event.is_set():
                break
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval_seconds)
            except (asyncio.TimeoutError, RuntimeError):
                # Normal timeout or loop change, continue loop
                pass
            except asyncio.CancelledError:
                break
