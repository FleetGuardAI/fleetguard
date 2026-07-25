"""
FleetGuard — Kafka Event Bus
Implementation of the EventBus interface using aiokafka.
"""

import logging
from typing import Any
try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None

from infrastructure.events.bus import EventBus
from infrastructure.events.serialization import EventSerializer
from schemas.operational_event import OperationalEventResponse

logger = logging.getLogger("fleetguard.infrastructure.kafka_bus")


class KafkaEventBus(EventBus):
    """
    Kafka-backed event publisher.
    """
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self._producer = None
        self._is_running = False

    async def start(self) -> None:
        if not self._is_running:
            logger.info(f"Starting Kafka producer (bootstrap_servers={self.bootstrap_servers})...")
            self._producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
            await self._producer.start()
            self._is_running = True
            logger.info("Kafka producer started.")

    async def stop(self) -> None:
        if self._is_running:
            logger.info("Stopping Kafka producer...")
            await self._producer.stop()
            self._is_running = False
            logger.info("Kafka producer stopped.")

    async def publish(self, topic: str, event: Any) -> None:
        if not self._is_running:
            logger.warning("Kafka producer is not running. Attempting to start...")
            await self.start()
            
        if isinstance(event, OperationalEventResponse):
            serialized = EventSerializer.serialize(event)
            # Use event_id as the partition key to ensure events for the same entity 
            # (or exact same event) go to the same partition.
            key = str(event.id).encode("utf-8")
            await self._producer.send_and_wait(topic, value=serialized, key=key)
            logger.debug(f"Published event {event.id} to topic {topic}")
        else:
            logger.error(f"Cannot publish event of type {type(event)}. Only OperationalEventResponse is supported.")
