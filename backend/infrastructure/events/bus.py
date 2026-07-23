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
