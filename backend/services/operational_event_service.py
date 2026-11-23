"""
FleetGuard — Operational Event Service

The single point of entry for all modules that need to create or query
Operational Events.

Responsibilities
----------------
• Accept Pydantic schemas from callers (routers, future modules).
• Construct ORM instances and delegate persistence to the repository.
• Convert ORM instances back to Pydantic response schemas before returning.
• Translate repository domain exceptions into service-level exceptions.
• Provide clearly named extension points for future integrations
  (Validation & Enrichment Engine, Event Dispatcher, Fleet Memory).

This service does NOT:
• Write SQL or interact with the database directly.
• Implement business intelligence or analytics.
• Validate event payloads (that is the Validation & Enrichment Engine's job).
• Dispatch events to downstream processors (that is the Event Dispatcher's job).
• Raise HTTP exceptions (that responsibility belongs to the router layer).

Dependency Injection
--------------------
The service accepts an ``AsyncSession`` at construction time, following the
same pattern used by ``auth_service.py`` and the repository layer.

Usage from a router::

    from services.operational_event_service import OperationalEventService
    from database import get_db

    @router.post("/events", response_model=OperationalEventResponse)
    async def submit_event(
        payload: OperationalEventCreate,
        db: AsyncSession = Depends(get_db),
    ) -> OperationalEventResponse:
        service = OperationalEventService(db)
        return await service.create_event(payload)

Wired integrations
------------------
    _after_create(event)  → EventDispatcher.publish()  (this milestone)

Pending stubs
-------------
    _before_status_change(...)  ← Validation & Enrichment Engine guard
    _on_metadata_update(...)    ← Enrichment Engine audit hook
"""

from __future__ import annotations

import uuid
import logging
from typing import Any, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork
from config import settings

from models.operational_event import (
    CaptureMethod,
    EntityType,
    EventType,
    OperationalEvent,
    VerificationStatus,
)
from models.outbox_event import OutboxStatus
from repositories.operational_event_repository import (
    EventNotFoundError,
    EventPersistenceError,
    OperationalEventRepository,
)
from schemas.operational_event import (
    OperationalEventCreate,
    OperationalEventResponse,
    OperationalEventUpdate,
)

logger = logging.getLogger("fleetguard.services.operational_event")


# ---------------------------------------------------------------------------
# Service-level Exceptions
# ---------------------------------------------------------------------------

class EventServiceError(Exception):
    """
    Base class for all errors raised by ``OperationalEventService``.

    Routers should catch this and return an appropriate HTTP response.
    Subclasses carry more specific context.
    """


class EventNotFound(EventServiceError):
    """Raised when a requested event does not exist."""

    def __init__(self, event_id: uuid.UUID | str) -> None:
        self.event_id = event_id
        super().__init__(f"Operational event '{event_id}' not found.")


class EventWriteError(EventServiceError):
    """Raised when a write operation fails at the persistence layer."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Event write error: {detail}")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class OperationalEventService:
    """
    Coordinates all Operational Event operations for the FleetGuard platform.

    Every module that needs to record or query fleet events should call this
    service.  No module should instantiate the repository directly.

    Parameters
    ----------
    db : AsyncSession
        An active SQLAlchemy async session, injected via ``Depends(get_db)``.
    """

    def __init__(
        self,
        uow: Any,
        dispatcher: Optional[Any] = None,
    ) -> None:
        if hasattr(uow, "repositories"):
            self.uow = uow
        else:
            # Fallback wrapper for raw AsyncSession
            from infrastructure.uow import RepositoryRegistry
            class _SessionUoW(AbstractUnitOfWork):
                def __init__(self, s):
                    self.session = s
                    self.repositories = RepositoryRegistry(s)
                async def commit(self):
                    await self.session.commit()
                async def rollback(self):
                    await self.session.rollback()
            self.uow = _SessionUoW(uow)
        self.dispatcher = dispatcher

    # -----------------------------------------------------------------------
    # Write Operations
    # -----------------------------------------------------------------------

    async def create_event(
        self,
        company_id_or_payload: int | OperationalEventCreate,
        payload: Optional[OperationalEventCreate] = None,
    ) -> OperationalEventResponse:
        """
        Record a new Operational Event.

        Accepts either (company_id, payload) or (payload) where company_id
        is embedded in payload or defaulted.
        """
        if isinstance(company_id_or_payload, OperationalEventCreate):
            event_payload = company_id_or_payload
            company_id = getattr(event_payload, "company_id", None) or 1
        else:
            company_id = int(company_id_or_payload)
            if payload is None:
                raise ValueError("OperationalEventCreate payload must be provided")
            event_payload = payload

        event = OperationalEvent(
            event_type=event_payload.event_type,
            entity_type=event_payload.entity_type,
            entity_id=event_payload.entity_id,
            occurred_at=event_payload.occurred_at,
            capture_method=event_payload.capture_method,
            created_by=event_payload.created_by,
            payload=event_payload.payload,
            event_metadata=event_payload.event_metadata,
            notes=event_payload.notes,
            company_id=company_id,
        )

        try:
            persisted = await self.uow.repositories.operational_event.create_event(event)
        except EventPersistenceError as exc:
            logger.error("create_event failed: %s", exc.detail)
            raise EventWriteError(exc.detail) from exc

        event_id_str = str(persisted.id)
        logger.info(
            "Event created: id=%s type=%s entity=%s:%s company_id=%s",
            event_id_str,
            persisted.event_type.value,
            persisted.entity_type.value,
            persisted.entity_id,
            persisted.company_id,
        )

        response = OperationalEventResponse.model_validate(persisted)

        # Stage the event in the Outbox to guarantee delivery.
        # In no-Kafka mode with an active in-process dispatcher, stage with status PUBLISHING
        # to claim the record immediately, preventing competing polling workers from dispatching concurrently.
        initial_status = (
            OutboxStatus.PUBLISHING
            if (not getattr(settings, "KAFKA_ENABLED", False) and self.dispatcher is not None)
            else OutboxStatus.PENDING
        )

        outbox_payload = response.model_dump(mode="json")
        await self.uow.repositories.outbox.create_event(
            topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
            payload=outbox_payload,
            event_id=event_id_str,
            status=initial_status,
        )

        await self.uow.commit()

        # In-process dispatch if a dispatcher is registered
        if self.dispatcher is not None:
            try:
                await self.dispatcher.publish(response)
                # Successful in-process dispatch -> advance outbox state to PUBLISHED
                if not getattr(settings, "KAFKA_ENABLED", False):
                    try:
                        outbox_record = await self.uow.repositories.outbox.get_by_event_id(event_id_str)
                        if outbox_record:
                            await self.uow.repositories.outbox.mark_published(outbox_record)
                            await self.uow.commit()
                    except Exception as outbox_err:
                        logger.warning("Could not advance outbox state for event %s: %s", event_id_str, outbox_err)
            except Exception as exc:
                logger.exception("In-process dispatch failed for event %s: %s", event_id_str, exc)
                # Dispatch failed -> release claim back to PENDING for the background worker to retry
                if not getattr(settings, "KAFKA_ENABLED", False):
                    try:
                        outbox_record = await self.uow.repositories.outbox.get_by_event_id(event_id_str)
                        if outbox_record:
                            await self.uow.repositories.outbox.mark_failed(outbox_record, str(exc))
                            await self.uow.commit()
                    except Exception as failure_err:
                        logger.error("Could not record dispatch failure for event %s: %s", event_id_str, failure_err)

        return response

    async def update_notes(
        self,
        event_id: uuid.UUID,
        company_id: int,
        notes: str | None,
    ) -> OperationalEventResponse:
        """
        Update the free-text annotation of an existing event.

        Parameters
        ----------
        event_id : uuid.UUID
            UUID of the event to update.
        company_id : int
            The tenant boundary.
        notes : str | None
            New annotation text.  Pass ``None`` to clear.

        Returns
        -------
        OperationalEventResponse
            The updated event.

        Raises
        ------
        EventNotFound
            If the event does not exist.
        EventWriteError
            If the update cannot be persisted.
        """
        try:
            updated = await self.uow.repositories.operational_event.update_event_notes(event_id, company_id, notes)
        except EventNotFoundError as exc:
            raise EventNotFound(event_id) from exc
        except EventPersistenceError as exc:
            raise EventWriteError(exc.detail) from exc

        return OperationalEventResponse.model_validate(updated)

    async def update_metadata(
        self,
        event_id: uuid.UUID,
        company_id: int,
        event_metadata: dict[str, Any],
    ) -> OperationalEventResponse:
        """
        Replace the ``event_metadata`` JSONB field of an existing event.

        Intended for the Validation & Enrichment Engine to annotate events
        with processing context after they are captured.

        Extension point
        ---------------
        ``_on_metadata_update`` is called after a successful update.

        Parameters
        ----------
        event_id : uuid.UUID
            UUID of the event to update.
        company_id : int
            The tenant boundary.
        event_metadata : dict[str, Any]
            New metadata payload.  Replaces the existing value entirely.

        Returns
        -------
        OperationalEventResponse
            The updated event.

        Raises
        ------
        EventNotFound
            If the event does not exist.
        EventWriteError
            If the update cannot be persisted.
        """
        try:
            updated = await self.uow.repositories.operational_event.update_event_metadata(event_id, company_id, event_metadata)
        except EventNotFoundError as exc:
            raise EventNotFound(event_id) from exc
        except EventPersistenceError as exc:
            raise EventWriteError(exc.detail) from exc

        # Extension point — Enrichment Engine audit hook (not yet implemented)
        await self._on_metadata_update(updated)

        return OperationalEventResponse.model_validate(updated)

    async def apply_update(
        self,
        event_id: uuid.UUID,
        company_id: int,
        update: OperationalEventUpdate,
    ) -> OperationalEventResponse:
        """
        Apply a partial update to an event using the ``OperationalEventUpdate``
        schema.

        Handles ``verification_status`` and ``notes`` updates in a single call.
        Only fields that are not ``None`` in the schema are applied.

        This is the method a router should call for ``PATCH /events/{id}``
        requests.

        Parameters
        ----------
        event_id : uuid.UUID
            UUID of the event to update.
        company_id : int
            The tenant boundary.
        update : OperationalEventUpdate
            Partial update schema.  Fields left as ``None`` are not changed.

        Returns
        -------
        OperationalEventResponse
            The event state after all updates have been applied.

        Raises
        ------
        EventNotFound
            If the event does not exist.
        EventWriteError
            If any update cannot be persisted.
        """
        try:
            if update.verification_status is not None:
                # Extension point — Validation Engine guard (not yet implemented)
                await self._before_status_change(event_id, update.verification_status)
                await self.uow.repositories.operational_event.update_verification_status(
                    event_id, company_id, update.verification_status
                )

            if update.notes is not None:
                await self.uow.repositories.operational_event.update_event_notes(event_id, company_id, update.notes)

            event = await self.uow.repositories.operational_event.get_event_by_id(event_id, company_id)

        except EventNotFoundError as exc:
            raise EventNotFound(event_id) from exc
        except EventPersistenceError as exc:
            raise EventWriteError(exc.detail) from exc

        return OperationalEventResponse.model_validate(event)

    # -----------------------------------------------------------------------
    # Read Operations
    # -----------------------------------------------------------------------

    async def get_event(
        self,
        event_id: uuid.UUID | str,
        company_id: Optional[int] = None,
    ) -> OperationalEventResponse:
        """
        Retrieve a single event by its UUID.

        Parameters
        ----------
        event_id : uuid.UUID | str
            UUID of the event to retrieve.
        company_id : Optional[int]
            The tenant boundary if scoped, or None for internal processing.

        Returns
        -------
        OperationalEventResponse
            The matching event.

        Raises
        ------
        EventNotFound
            If no event with the given UUID exists.
        """
        try:
            event = await self.uow.repositories.operational_event.get_event_by_id(event_id, company_id)
        except EventNotFoundError as exc:
            raise EventNotFound(event_id) from exc

        return OperationalEventResponse.model_validate(event)

    async def list_events(
        self,
        company_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationalEventResponse]:
        """
        Return a paginated list of all events, most recent first.

        Parameters
        ----------
        company_id : int
            The tenant boundary.
        limit : int
            Maximum records to return.  Default 50.
        offset : int
            Records to skip.  Default 0.

        Returns
        -------
        Sequence[OperationalEventResponse]
            Ordered list of event responses.
        """
        events = await self.uow.repositories.operational_event.list_events(company_id=company_id, limit=limit, offset=offset)
        return [OperationalEventResponse.model_validate(e) for e in events]

    async def list_events_by_entity(
        self,
        company_id: int,
        entity_type: EntityType,
        entity_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationalEventResponse]:
        """
        Return all events for a specific fleet entity.

        Example: all events for vehicle ``MH12AB1234``.

        Parameters
        ----------
        company_id : int
            The tenant boundary.
        entity_type : EntityType
            Domain category of the entity (VEHICLE, DRIVER, etc.).
        entity_id : str
            Identifier of the specific entity.
        limit : int
            Maximum records to return.  Default 50.
        offset : int
            Records to skip.  Default 0.

        Returns
        -------
        Sequence[OperationalEventResponse]
            Events for the entity, ordered by ``occurred_at`` desc.
        """
        events = await self.uow.repositories.operational_event.list_events_by_entity(
            company_id, entity_type, entity_id, limit=limit, offset=offset
        )
        return [OperationalEventResponse.model_validate(e) for e in events]

    async def list_events_by_type(
        self,
        company_id: int,
        event_type: EventType,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationalEventResponse]:
        """
        Return all events of a specific event type.

        Example: all ``FUEL_FILLED`` events across the fleet.

        Parameters
        ----------
        company_id : int
            The tenant boundary.
        event_type : EventType
            The event type to filter by.
        limit : int
            Maximum records to return.  Default 50.
        offset : int
            Records to skip.  Default 0.

        Returns
        -------
        Sequence[OperationalEventResponse]
            Matching events ordered by ``occurred_at`` desc.
        """
        events = await self.uow.repositories.operational_event.list_events_by_type(
            company_id, event_type, limit=limit, offset=offset
        )
        return [OperationalEventResponse.model_validate(e) for e in events]

    async def list_events_by_verification_status(
        self,
        company_id: int,
        status: VerificationStatus,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationalEventResponse]:
        """
        Return all events in a given verification state.

        Primarily consumed by the Validation & Enrichment Engine to fetch
        the ``PENDING`` queue, and by fleet managers reviewing ``DISPUTED``
        events.

        Parameters
        ----------
        company_id : int
            The tenant boundary.
        status : VerificationStatus
            The verification status to filter by.
        limit : int
            Maximum records to return.  Default 50.
        offset : int
            Records to skip.  Default 0.

        Returns
        -------
        Sequence[OperationalEventResponse]
            Matching events ordered by ``occurred_at`` desc.
        """
        events = await self.uow.repositories.operational_event.list_events_by_verification_status(
            company_id, status, limit=limit, offset=offset
        )
        return [OperationalEventResponse.model_validate(e) for e in events]

    # -----------------------------------------------------------------------

    async def _before_status_change(
        self,
        event_id: uuid.UUID,
        new_status: VerificationStatus,
    ) -> None:
        """
        Hook called before a ``verification_status`` transition is committed.

        Future integrations
        -------------------
        • Validation & Enrichment Engine — enforce state machine rules and
          reject invalid transitions (e.g. VERIFIED → PENDING).

        Do NOT raise HTTP exceptions here.  Raise a domain exception that
        the router translates.
        """
        pass  # Not yet implemented — wired in Validation Engine milestone

    async def _on_metadata_update(self, event: OperationalEvent) -> None:
        """
        Hook called after ``event_metadata`` has been successfully updated.

        Future integrations
        -------------------
        • Validation & Enrichment Engine — audit that processing metadata
          was correctly written.
        • Fleet Memory — re-evaluate entity state if metadata carries
          enrichment signals.
        """
        pass  # Not yet implemented — wired in Validation Engine milestone
