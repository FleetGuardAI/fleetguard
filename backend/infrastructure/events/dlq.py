"""
FleetGuard — Dead Letter Queue Publisher
Responsible for publishing DeadLetterMessage to the DLQ Kafka topic.
"""

import logging

from config import settings
from infrastructure.events.bus import EventBus
from schemas.dlq import DeadLetterMessage

logger = logging.getLogger("fleetguard.infrastructure.dlq")

class DeadLetterPublisher:
    """
    Publishes forensic records of unprocessable messages to the Dead Letter Queue.
    Contains strictly no retry or business logic.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def publish(self, msg: DeadLetterMessage) -> None:
        """
        Publishes the given DeadLetterMessage to the configured DLQ topic.
        If this fails, the exception must bubble up to the caller to prevent 
        the consumer from committing the offset, ensuring the message can be 
        retried organically upon restart.
        """
        logger.info(
            f"Publishing DeadLetterMessage to DLQ topic '{settings.DLQ_TOPIC_NAME}' "
            f"(Origin: {msg.original_topic}[{msg.original_partition}]@{msg.original_offset})"
        )
        
        # event_bus.publish accepts Pydantic models and serializes them to JSON
        await self.event_bus.publish(
            topic=settings.DLQ_TOPIC_NAME,
            event=msg
        )
