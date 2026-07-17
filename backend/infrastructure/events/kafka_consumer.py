"""
FleetGuard — Kafka Consumer Infrastructure
Runs an asyncio loop to consume messages from Kafka and dispatches them 
to a single registered EventSubscriber.
"""

import asyncio
import logging
from typing import Any
from datetime import datetime, timezone
from aiokafka import AIOKafkaConsumer

from dispatchers.event_subscriber import EventSubscriber
from infrastructure.events.serialization import EventSerializer
from infrastructure.events.retry import (
    RetryPolicy,
    RetryExecutor,
    RetryContext,
    NonRetryableError,
    RetriesExhaustedError,
)
from infrastructure.events.dlq import DeadLetterPublisher
from schemas.dlq import DeadLetterMessage, FailureCategory
from schemas.operational_event import OperationalEventResponse
import traceback

logger = logging.getLogger("fleetguard.infrastructure.kafka_consumer")


class KafkaConsumerRunner:
    """
    Consumes messages from a Kafka topic and routes them to a single EventSubscriber.
    """
    def __init__(
        self, 
        bootstrap_servers: str, 
        group_id: str, 
        topic: str, 
        subscriber: EventSubscriber,
        retry_policy: RetryPolicy = None,
        dlq_publisher: DeadLetterPublisher = None,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topic = topic
        self.subscriber = subscriber
        self.dlq_publisher = dlq_publisher
        self.retry_executor = RetryExecutor(retry_policy or RetryPolicy())
        
        self._consumer = None
        self._running = False
        self._task = None

    async def start(self) -> None:
        if self._running:
            return
            
        logger.info(f"Starting Kafka consumer for group '{self.group_id}' on topic '{self.topic}'...")
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False  # We manually commit after successful processing
        )
        await self._consumer.start()
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(f"Kafka consumer '{self.group_id}' started.")

    async def stop(self) -> None:
        if not self._running:
            return
            
        logger.info(f"Stopping Kafka consumer '{self.group_id}'...")
        self._running = False
        
        if self._task:
            try:
                # Wait for the consumer loop to gracefully exit
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning(f"Kafka consumer '{self.group_id}' did not shut down gracefully. Forcing cancellation.")
                self._task.cancel()
            except asyncio.CancelledError:
                pass
        
        if self._consumer:
            await self._consumer.stop()
            
        logger.info(f"Kafka consumer '{self.group_id}' stopped.")

    async def _consume_loop(self) -> None:
        try:
            # Note: We do not use `async for msg in self._consumer` directly here
            # because we want to frequently check `self._running` for graceful shutdown.
            while self._running:
                try:
                    # Poll for a single message with a timeout to allow checking `self._running`
                    result = await self._consumer.getmany(timeout_ms=1000, max_records=1)
                    
                    if not result:
                        continue
                        
                    # getmany returns a dict of {TopicPartition: [ConsumerRecord]}
                    # Since we requested max_records=1, we can just extract it.
                    for tp, messages in result.items():
                        for msg in messages:
                            if not self._running:
                                break
                                
                            await self._process_message(msg)
                            
                except Exception as e:
                    logger.error(f"Kafka consumer '{self.group_id}' encountered a polling error: {e}")
                    await asyncio.sleep(5)  # Backoff before retrying poll
                    
        except asyncio.CancelledError:
            logger.info(f"Consumer loop for '{self.group_id}' was forcefully cancelled.")

    async def _process_message(self, msg: Any) -> None:
        """
        Deserializes the message, dispatches it to the subscriber, and commits the offset.
        Guarantees that offsets are ONLY committed upon total success.
        """
        # 1. Deserialization
        try:
            event = EventSerializer.deserialize(msg.value)
        except Exception as e:
            logger.error(f"Failed to deserialize Kafka message at offset {msg.offset}: {e}")
            await self._handle_poison_pill(msg, e)
            return

        # 2. Filtering
        if self.subscriber.event_filter is not None and event.event_type not in self.subscriber.event_filter:
            # Message is filtered out; safe to commit offset and skip
            await self._consumer.commit()
            return

        # 3. Processing
        try:
            await self.retry_executor.execute(self.subscriber.handle, event)
        except NonRetryableError as e:
            logger.error(f"Subscriber '{self.subscriber.name}' encountered Non-Retryable Error for event {event.id}: {e}")
            await self._handle_processing_failure(msg, event, e.original_exception)
            return
        except RetriesExhaustedError as e:
            logger.error(f"Subscriber '{self.subscriber.name}' exhausted retries for event {event.id}: {e}")
            await self._handle_processing_failure(msg, event, e.original_exception, e.context)
            return
        except Exception as e:
            # Fallback for completely unhandled logic (should be caught by Executor typically)
            logger.error(f"Subscriber '{self.subscriber.name}' failed unexpectedly for event {event.id}: {e}")
            await self._handle_processing_failure(msg, event, e)
            return

        # 4. Commit Offset
        # We only reach this point if deserialization and processing completely succeeded
        await self._consumer.commit()
        logger.debug(f"Consumer '{self.group_id}' committed offset {msg.offset}")

    # =========================================================================
    # Extension Points (Future Milestones)
    # =========================================================================

    async def _handle_poison_pill(self, msg: Any, error: Exception) -> None:
        """
        Triggered when an event fails deserialization.
        Routes to DLQ and commits offset only if publish succeeds.
        """
        logger.critical(f"POISON PILL in group '{self.group_id}'. Offset {msg.offset} is unprocessable.")
        
        if not self.dlq_publisher:
            logger.warning(f"No DLQ Publisher configured for {self.group_id}. Stalling consumer.")
            await asyncio.sleep(5)
            return
            
        try:
            # Get raw payload. msg.value is bytes.
            payload_str = msg.value.decode("utf-8", errors="replace") if msg.value else ""
            
            dlq_msg = DeadLetterMessage(
                original_topic=msg.topic,
                original_partition=msg.partition,
                original_offset=msg.offset,
                event_id=None,
                payload=payload_str,
                failure_category=FailureCategory.DESERIALIZATION,
                exception_type=type(error).__name__,
                exception_message=str(error),
                stack_trace=traceback.format_exc() if settings.DLQ_INCLUDE_STACK_TRACE else None,
                retry_attempts=0,
                failed_at=datetime.now(timezone.utc),
                consumer_name=self.group_id
            )
            
            await self.dlq_publisher.publish(dlq_msg)
            await self._consumer.commit()
            
        except Exception as e:
            logger.error(f"Failed to publish Poison Pill to DLQ: {e}. Consumer stalling.")
            await asyncio.sleep(5)

    def _categorize_error(self, error: Exception) -> FailureCategory:
        """Heuristically categorize exceptions for DLQ metrics."""
        err_str = type(error).__name__.lower()
        if "timeout" in err_str:
            return FailureCategory.TIMEOUT
        if "connection" in err_str or "network" in err_str:
            return FailureCategory.NETWORK
        if "sql" in err_str or "database" in err_str or "db" in err_str:
            return FailureCategory.DATABASE
        if "validation" in err_str or "pydantic" in err_str:
            return FailureCategory.VALIDATION
        return FailureCategory.UNKNOWN

    async def _handle_processing_failure(
        self, 
        msg: Any, 
        event: OperationalEventResponse, 
        error: Exception, 
        context: RetryContext = None
    ) -> None:
        """
        Triggered when a subscriber throws an error and all retries are exhausted.
        Routes to DLQ and commits offset only if publish succeeds.
        """
        logger.error(f"PROCESSING FAILURE in group '{self.group_id}' for event {event.id}.")
        
        if not self.dlq_publisher:
            logger.warning(f"No DLQ Publisher configured for {self.group_id}. Stalling consumer.")
            await asyncio.sleep(5)
            return
            
        try:
            # We don't truncate the payload, as requested
            payload_str = msg.value.decode("utf-8", errors="replace") if msg.value else ""
            
            dlq_msg = DeadLetterMessage(
                original_topic=msg.topic,
                original_partition=msg.partition,
                original_offset=msg.offset,
                event_id=str(event.id),
                payload=payload_str,
                failure_category=self._categorize_error(error),
                exception_type=type(error).__name__,
                exception_message=str(error),
                stack_trace=traceback.format_exc() if settings.DLQ_INCLUDE_STACK_TRACE else None,
                retry_attempts=context.current_attempt if context else 0,
                failed_at=datetime.now(timezone.utc),
                consumer_name=self.group_id
            )
            
            await self.dlq_publisher.publish(dlq_msg)
            await self._consumer.commit()
            
        except Exception as e:
            logger.error(f"Failed to publish to DLQ for event {event.id}: {e}. Consumer stalling.")
            await asyncio.sleep(5)
