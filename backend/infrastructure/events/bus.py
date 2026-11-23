"""
FleetGuard — Event Bus Interface
Abstract base class for all event transport implementations.
"""

from abc import ABC, abstractmethod
from typing import Any

class EventBus(ABC):
    """
    Abstract interface for publishing events to the transport layer.
    """

    @abstractmethod
    async def publish(self, topic: str, event: Any) -> None:
        """
        Publish an event to a specified topic.

        Parameters
        ----------
        topic : str
            The topic or channel name to publish the event to.
        event : Any
            The event object (e.g., OperationalEventResponse) to publish.
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """
        Initialize and connect the event bus.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Cleanly disconnect and shut down the event bus.
        """
        pass


class InProcessEventBus(EventBus):
    """
    In-process EventBus implementation that dispatches to EventDispatcher.
    Allows OutboxPublisher to relay pending outbox events even when Kafka is disabled,
    guaranteeing durability and crash-recovery across all environments.
    """
    def __init__(self, dispatcher=None):
        self._dispatcher = dispatcher

    @property
    def dispatcher(self):
        if self._dispatcher is None:
            from dispatchers.event_dispatcher import default_dispatcher
            self._dispatcher = default_dispatcher
        return self._dispatcher

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def publish(self, topic: str, event: Any) -> None:
        from schemas.operational_event import OperationalEventResponse
        if isinstance(event, dict):
            event = OperationalEventResponse.model_validate(event)
        if isinstance(event, OperationalEventResponse):
            await self.dispatcher.publish(event)
        else:
            raise TypeError(f"Cannot publish event of type {type(event)}. Only OperationalEventResponse or dict is supported.")
