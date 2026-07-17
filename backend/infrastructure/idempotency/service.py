"""
FleetGuard — Idempotency Service
Provides a generic duplicate-event detection framework for all Business Domains.
"""

import logging
from typing import Any, Optional
from infrastructure.uow import AbstractUnitOfWork

logger = logging.getLogger("fleetguard.infrastructure.idempotency")


class IdempotencyService:
    """
    Coordinates Idempotency checks.
    """
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def has_processed(self, event_id: str, domain_name: str) -> bool:
        """
        Check if the domain has already processed this Operational Event.
        """
        is_processed = await self.uow.repositories.idempotency.has_processed(event_id, domain_name)
        if is_processed:
            logger.debug(f"Idempotency hit: Domain {domain_name} already processed event {event_id}")
        return is_processed

    async def mark_processed(
        self, 
        event_id: str, 
        domain_name: str, 
        result: str = "SUCCESS",
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Record the successful processing of an Operational Event.
        This writes to the DB session, which should be committed atomically 
        along with the Business Domain's state changes.
        """
        await self.uow.repositories.idempotency.mark_processed(event_id, domain_name, result, metadata)
        logger.debug(f"Idempotency saved: Domain {domain_name} marked event {event_id} as processed.")
