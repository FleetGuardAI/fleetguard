"""
FleetGuard — Event Dispatcher

Delivers newly persisted Operational Events to all registered subscribers.

The dispatcher is an in-process pub/sub bus.  It is intentionally simple:
no persistence, no retry, no dead-letter queue.  All of those concerns belong
to a future external message broker (Kafka, RabbitMQ, Redis Streams).

Responsibilities
----------------
• Maintain a registry of ``EventSubscriber`` instances.
• For each published event, invoke every subscriber whose ``event_filter``
  passes the event's ``event_type``.
• Catch and log subscriber exceptions so one bad subscriber cannot prevent
  others from receiving the event.
• Never know anything about the domain (vehicles, drivers, fuel, etc.).

What the dispatcher does NOT do
---------------------------------
• It does not validate events.
• It does not retry failed subscribers.
• It does not guarantee ordering.
• It does not buffer or persist events.
• It does not know what subscribers do with events.

Replacement strategy (future)
------------------------------
When the platform scales to require an external broker, this dispatcher is
replaced by a thin adapter (e.g. ``KafkaEventDispatcher``) that publishes to
a topic instead of calling subscriber ``handle()`` methods directly.  All
callers — specifically ``OperationalEventService._after_create`` — need only
swap the injected dispatcher type.  Business code is unchanged.

Application Lifecycle
---------------------
A single ``EventDispatcher`` instance is created in ``main.py`` at startup
and injected into ``OperationalEventService`` via the ``get_event_service``
FastAPI dependency.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dispatchers.event_subscriber import EventSubscriber

if TYPE_CHECKING:
    from schemas.operational_event import OperationalEventResponse

logger = logging.getLogger("fleetguard.dispatchers.event_dispatcher")


class EventDispatcher:
    """
    In-process event dispatcher.

    Subscribers register with ``register_subscriber()`` and are called
    in registration order whenever ``publish()`` is invoked.

    Thread safety
    -------------
    This implementation is designed for use within a single asyncio event loop
    (the FastAPI process).  It is not thread-safe.  If background threads are
    added in future, protect ``_subscribers`` with an ``asyncio.Lock``.

    Usage
    -----
    ::

        dispatcher = EventDispatcher()
        dispatcher.register_subscriber(MySubscriber())

        # Later, after an event is persisted:
        await dispatcher.publish(event_response)
    """

    def __init__(self) -> None:
        # Ordered list of registered subscribers.
        # Using a list (not a set) to preserve registration order and
        # to allow the same subscriber type to register multiple instances
        # under different names if needed.
        self._subscribers: list[EventSubscriber] = []

    # -----------------------------------------------------------------------
    # Registration
    # -----------------------------------------------------------------------

    def register_subscriber(self, subscriber: EventSubscriber) -> None:
        """
        Register a new subscriber.

        The subscriber will receive events from this point forward.  Events
        published before registration are not delivered retroactively.

        Parameters
        ----------
        subscriber : EventSubscriber
            The subscriber instance to register.

        Raises
        ------
        ValueError
            If a subscriber with the same ``name`` is already registered.
            Names must be unique to enable targeted unregistration.
        """
        for existing in self._subscribers:
            if existing.name == subscriber.name:
                raise ValueError(
                    f"A subscriber named '{subscriber.name}' is already registered. "
                    "Unregister the existing one first, or use a unique name."
                )
        self._subscribers.append(subscriber)
        logger.info(
            "Subscriber registered: name='%s' filter=%s",
            subscriber.name,
            (
                {e.value for e in subscriber.event_filter}
                if subscriber.event_filter
                else "ALL"
            ),
        )

    def unregister_subscriber(self, name: str) -> None:
        """
        Unregister a subscriber by name.

        After unregistration the subscriber will not receive any further events.

        Parameters
        ----------
        name : str
            The ``name`` attribute of the subscriber to remove.

        Raises
        ------
        KeyError
            If no subscriber with the given name is registered.
        """
        before = len(self._subscribers)
        self._subscribers = [s for s in self._subscribers if s.name != name]
        if len(self._subscribers) == before:
            raise KeyError(
                f"No subscriber named '{name}' is currently registered."
            )
        logger.info("Subscriber unregistered: name='%s'", name)

    @property
    def subscriber_names(self) -> list[str]:
        """Return a list of currently registered subscriber names."""
        return [s.name for s in self._subscribers]

    # -----------------------------------------------------------------------
    # Publishing
    # -----------------------------------------------------------------------

    async def publish(self, event: "OperationalEventResponse") -> None:
        """
        Deliver an event to all matching subscribers.

        Each subscriber whose ``event_filter`` matches (or is ``None``) is
        called in registration order.  Exceptions raised by individual
        subscribers are caught, logged, and do NOT prevent other subscribers
        from receiving the event.

        This method is a coroutine so that async subscribers (e.g. ones that
        write to another database or call an internal API) can be awaited
        directly without blocking the event loop.

        Parameters
        ----------
        event : OperationalEventResponse
            The fully validated Pydantic response schema of the persisted event.

        Notes
        -----
        If no subscribers are registered (or none match the event type),
        this method returns silently with a DEBUG log.
        """
        matching = self._matching_subscribers(event)

        if not matching:
            logger.debug(
                "No subscribers for event_type=%s — skipping dispatch.",
                event.event_type.value,
            )
            return

        logger.debug(
            "Dispatching event id=%s type=%s to %d subscriber(s).",
            event.id,
            event.event_type.value,
            len(matching),
        )

        for subscriber in matching:
            try:
                await subscriber.handle(event)
            except Exception as exc:  # noqa: BLE001
                # A failing subscriber must not block others or propagate to
                # the caller.  Log the full traceback for debugging.
                logger.exception(
                    "Subscriber '%s' raised an exception for event id=%s: %s",
                    subscriber.name,
                    event.id,
                    exc,
                )

    # -----------------------------------------------------------------------
    # Introspection (useful for tests and health checks)
    # -----------------------------------------------------------------------

    def __len__(self) -> int:
        """Return the number of registered subscribers."""
        return len(self._subscribers)

    def __repr__(self) -> str:
        return (
            f"<EventDispatcher subscribers={self.subscriber_names}>"
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _matching_subscribers(
        self, event: "OperationalEventResponse"
    ) -> list[EventSubscriber]:
        """
        Return only subscribers whose event_filter passes this event.

        A subscriber matches if:
          • Its ``event_filter`` is ``None`` (subscribe to everything), OR
          • The event's ``event_type`` is in its ``event_filter`` set.
        """
        return [
            s
            for s in self._subscribers
            if s.event_filter is None or event.event_type in s.event_filter
        ]
