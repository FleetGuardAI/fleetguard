"""
FleetGuard — Dispatchers Package

The dispatchers package provides the internal event publishing infrastructure.

Public surface
--------------
EventDispatcher   — in-process pub/sub bus; publish events to subscribers
EventSubscriber   — ABC that all subscribers must implement

Usage
-----
Register subscribers at application startup in ``main.py``::

    from dispatchers import EventDispatcher, EventSubscriber

    dispatcher = EventDispatcher()
    dispatcher.register_subscriber(MySubscriber())

Inject into the event service via the ``get_event_service`` dependency::

    def get_event_service(
        db: AsyncSession = Depends(get_db),
    ) -> OperationalEventService:
        return OperationalEventService(db, dispatcher=dispatcher)
"""

from dispatchers.event_dispatcher import EventDispatcher
from dispatchers.event_subscriber import EventSubscriber

__all__ = [
    "EventDispatcher",
    "EventSubscriber",
]
