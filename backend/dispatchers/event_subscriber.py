"""
FleetGuard — Event Subscriber Interface

Defines the contract that every subscriber to the EventDispatcher must implement.

A subscriber is any component that wants to react to Operational Events after
they have been persisted.  Examples of future subscribers:

  • Validation & Enrichment Engine  — advances PENDING → VERIFIED | REJECTED
  • Fleet Memory                    — updates Digital Twins
  • Fleet Intelligence Engine       — feeds the Finding Engine

Design principles
-----------------
• ``EventSubscriber`` is an abstract base class.  Every concrete subscriber
  must implement ``handle(event)``.
• Subscribers are pure infrastructure components.  They must NOT contain
  business intelligence, domain logic, or HTTP interactions.
• The ``event_filter`` property is optional.  When ``None``, the subscriber
  receives ALL event types.  When set, only events whose ``event_type`` is
  in the returned set are delivered.
• ``handle`` is async to support I/O-bound subscribers (e.g. writing to a
  second database, calling an internal API).  CPU-bound work should be
  offloaded with ``asyncio.to_thread`` inside the implementation.

Replacement strategy
--------------------
When FleetGuard moves to an external message broker (Kafka, RabbitMQ, Redis
Streams), concrete subscribers become consumers on those topics.  The
``EventSubscriber`` interface does not change — only the transport layer does.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.operational_event import OperationalEventResponse
    from models.operational_event import EventType


class EventSubscriber(ABC):
    """
    Abstract base class for all EventDispatcher subscribers.

    Subclass this and implement ``handle`` to react to Operational Events.

    Attributes
    ----------
    name : str
        Human-readable name for this subscriber.  Used in log output and
        for targeted unregistration.  Must be unique across registered
        subscribers.
    event_filter : frozenset[EventType] | None
        Optional set of ``EventType`` values this subscriber wants to
        receive.  If ``None``, the subscriber receives every event type.
        If set, only events whose ``event_type`` is in this set are
        delivered.

    Example
    -------
    ::

        class MySubscriber(EventSubscriber):
            name = "my_subscriber"
            event_filter = frozenset({EventType.FUEL_FILLED, EventType.TRIP_STARTED})

            async def handle(self, event: OperationalEventResponse) -> None:
                print(f"Received: {event.event_type} for {event.entity_id}")
    """

    #: Unique identifier for this subscriber.  Override in subclasses.
    name: str = "unnamed_subscriber"

    #: Optional event type filter.  ``None`` means subscribe to all types.
    event_filter: frozenset["EventType"] | None = None

    @abstractmethod
    async def handle(self, event: "OperationalEventResponse") -> None:
        """
        React to an Operational Event.

        Called by the dispatcher after every successful event persist that
        passes this subscriber's ``event_filter``.

        Parameters
        ----------
        event : OperationalEventResponse
            The fully validated Pydantic response schema of the persisted event.
            Read-only — do NOT mutate this object.

        Raises
        ------
        Exception
            Any exception raised here is caught by the dispatcher and logged.
            It does NOT propagate to the caller or roll back the transaction.
        """
        ...  # pragma: no cover
