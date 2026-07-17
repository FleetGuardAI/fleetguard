"""
FleetGuard — Operational Event Repository

Provides all database read/write access for the ``operational_events`` table.

Responsibilities
----------------
• Create new events.
• Retrieve events by various filter criteria.
• Update the mutable fields (notes, event_metadata, verification_status).
• Raise domain-level exceptions that services can handle and routers can
  translate into HTTP responses.

This repository does NOT:
• Implement business logic or validation rules.
• Raise HTTP exceptions (FastAPI-specific errors belong in the router layer).
• Know about Pydantic schemas — it works exclusively with ORM model instances.

Dependency Injection
--------------------
The repository accepts an ``AsyncSession`` at construction time.  Wire it in a
FastAPI router or service using the project-standard ``get_db`` dependency:

    @router.post("/events")
    async def submit_event(db: AsyncSession = Depends(get_db)):
        repo = OperationalEventRepository(db)
        event = await repo.create_event(...)

SQLAlchemy 2.x style
--------------------
All queries use the ``select()`` / ``execute()`` / ``scalars()`` API
introduced in SQLAlchemy 2.x.  Legacy ``session.query()`` is never used.
"""

from __future__ import annotations

import uuid
import logging
from typing import Any, Sequence

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models.operational_event import (
    EventType,
    EntityType,
    OperationalEvent,
    VerificationStatus,
)

logger = logging.getLogger("fleetguard.repositories.operational_event")


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------

class EventNotFoundError(Exception):
    """Raised when an event cannot be found by its ID."""

    def __init__(self, event_id: uuid.UUID) -> None:
        self.event_id = event_id
        super().__init__(f"OperationalEvent '{event_id}' not found.")


class EventPersistenceError(Exception):
    """Raised when a database write fails for an unexpected reason."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Event persistence error: {detail}")


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class OperationalEventRepository:
    """
    Data-access layer for the ``operational_events`` table.

    All methods are async-first and use the SQLAlchemy 2.x ``select()`` API.

    Parameters
    ----------
    db : AsyncSession
        An active SQLAlchemy async session, typically injected via
        ``Depends(get_db)`` in a FastAPI router or service.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # -----------------------------------------------------------------------
    # Write Methods
    # -----------------------------------------------------------------------

    async def create_event(self, event: OperationalEvent) -> OperationalEvent:
        """
        Persist a new Operational Event to the database.

        The ``event`` object must be a fully constructed ``OperationalEvent``
        ORM instance.  UUID generation and default field values are handled
        by the ORM model / database defaults.

        Parameters
        ----------
        event : OperationalEvent
            The event instance to persist.

        Returns
        -------
        OperationalEvent
            The persisted event with all server-generated fields populated
            (``id``, ``recorded_at``, ``created_at``, ``updated_at``).

        Raises
        ------
        EventPersistenceError
            On any unexpected database error.
        """
        try:
            self._db.add(event)
            await self._db.flush()
            await self._db.refresh(event)
            logger.info(
                "OperationalEvent created: id=%s type=%s entity=%s:%s",
                event.id,
                event.event_type.value,
                event.entity_type.value,
                event.entity_id,
            )
            return event
        except IntegrityError as exc:
            logger.error("create_event IntegrityError: %s", exc.orig)
            raise EventPersistenceError(
                "Failed to persist event — constraint violation."
            ) from exc
        except SQLAlchemyError as exc:
            logger.error("create_event SQLAlchemyError: %s", exc)
            raise EventPersistenceError(
                "Unexpected database error while creating event."
            ) from exc

    async def update_event_notes(
        self,
        event_id: uuid.UUID,
        notes: str | None,
    ) -> OperationalEvent:
        """
        Update the free-text ``notes`` field of an existing event.

        Notes is the only field intended for human annotation.  It is the
        only string field that may be mutated after creation.

        Parameters
        ----------
        event_id : uuid.UUID
            The UUID of the event to update.
        notes : str | None
            The new annotation text.  Pass ``None`` to clear the notes field.

        Returns
        -------
        OperationalEvent
            The updated event instance.

        Raises
        ------
        EventNotFoundError
            If no event with the given ID exists.
        EventPersistenceError
            On any unexpected database error.
        """
        event = await self._get_or_raise(event_id)
        try:
            event.notes = notes
            await self._db.flush()
            await self._db.refresh(event)
            logger.info("OperationalEvent notes updated: id=%s", event_id)
            return event
        except SQLAlchemyError as exc:
            logger.error("update_event_notes SQLAlchemyError: %s", exc)
            raise EventPersistenceError(
                f"Failed to update notes for event '{event_id}'."
            ) from exc

    async def update_event_metadata(
        self,
        event_id: uuid.UUID,
        event_metadata: dict[str, Any],
    ) -> OperationalEvent:
        """
        Replace the ``event_metadata`` JSONB field of an existing event.

        Intended for the Validation & Enrichment Engine to append processing
        metadata (e.g. enrichment timestamps, source trace IDs).

        Parameters
        ----------
        event_id : uuid.UUID
            The UUID of the event to update.
        event_metadata : dict[str, Any]
            The new metadata payload.  Replaces the existing value entirely.

        Returns
        -------
        OperationalEvent
            The updated event instance.

        Raises
        ------
        EventNotFoundError
            If no event with the given ID exists.
        EventPersistenceError
            On any unexpected database error.
        """
        event = await self._get_or_raise(event_id)
        try:
            event.event_metadata = event_metadata
            await self._db.flush()
            await self._db.refresh(event)
            logger.info("OperationalEvent metadata updated: id=%s", event_id)
            return event
        except SQLAlchemyError as exc:
            logger.error("update_event_metadata SQLAlchemyError: %s", exc)
            raise EventPersistenceError(
                f"Failed to update metadata for event '{event_id}'."
            ) from exc

    async def update_verification_status(
        self,
        event_id: uuid.UUID,
        status: VerificationStatus,
    ) -> OperationalEvent:
        """
        Advance the ``verification_status`` of an existing event.

        This is the only state transition that should be applied to events
        after creation.  The state machine (PENDING → VERIFIED/DISPUTED/REJECTED)
        is enforced at the service layer, not here.

        Parameters
        ----------
        event_id : uuid.UUID
            The UUID of the event to update.
        status : VerificationStatus
            The new verification status value.

        Returns
        -------
        OperationalEvent
            The updated event instance.

        Raises
        ------
        EventNotFoundError
            If no event with the given ID exists.
        EventPersistenceError
            On any unexpected database error.
        """
        event = await self._get_or_raise(event_id)
        try:
            event.verification_status = status
            await self._db.flush()
            await self._db.refresh(event)
            logger.info(
                "OperationalEvent status updated: id=%s status=%s",
                event_id,
                status.value,
            )
            return event
        except SQLAlchemyError as exc:
            logger.error("update_verification_status SQLAlchemyError: %s", exc)
            raise EventPersistenceError(
                f"Failed to update status for event '{event_id}'."
            ) from exc

    # -----------------------------------------------------------------------
    # Read Methods
    # -----------------------------------------------------------------------

    async def get_event_by_id(self, event_id: uuid.UUID) -> OperationalEvent:
        """
        Retrieve a single event by its UUID primary key.

        Parameters
        ----------
        event_id : uuid.UUID
            The UUID of the event to retrieve.

        Returns
        -------
        OperationalEvent
            The matching event instance.

        Raises
        ------
        EventNotFoundError
            If no event with the given ID exists.
        """
        return await self._get_or_raise(event_id)

    async def list_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationalEvent]:
        """
        Retrieve a paginated list of all events, ordered by ``occurred_at``
        descending (most recent first).

        Parameters
        ----------
        limit : int
            Maximum number of records to return.  Default 50.
        offset : int
            Number of records to skip.  Default 0.

        Returns
        -------
        Sequence[OperationalEvent]
            A sequence of event instances.
        """
        stmt = (
            select(OperationalEvent)
            .order_by(OperationalEvent.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def list_events_by_entity(
        self,
        entity_type: EntityType,
        entity_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationalEvent]:
        """
        Retrieve all events for a specific entity (e.g. all events for
        vehicle ``MH12AB1234``).

        Uses the composite index ``ix_operational_events_entity``
        (entity_type, entity_id) for efficient lookup.

        Parameters
        ----------
        entity_type : EntityType
            The domain category of the entity (e.g. VEHICLE, DRIVER).
        entity_id : str
            The identifier of the specific entity instance.
        limit : int
            Maximum number of records to return.  Default 50.
        offset : int
            Number of records to skip.  Default 0.

        Returns
        -------
        Sequence[OperationalEvent]
            Events for the specified entity, ordered by ``occurred_at`` desc.
        """
        stmt = (
            select(OperationalEvent)
            .where(
                OperationalEvent.entity_type == entity_type,
                OperationalEvent.entity_id == entity_id,
            )
            .order_by(OperationalEvent.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def list_events_by_type(
        self,
        event_type: EventType,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationalEvent]:
        """
        Retrieve all events of a given event type (e.g. all FUEL_FILLED events).

        Uses the ``ix_operational_events_event_type`` index.

        Parameters
        ----------
        event_type : EventType
            The event type to filter by.
        limit : int
            Maximum number of records to return.  Default 50.
        offset : int
            Number of records to skip.  Default 0.

        Returns
        -------
        Sequence[OperationalEvent]
            Matching events ordered by ``occurred_at`` desc.
        """
        stmt = (
            select(OperationalEvent)
            .where(OperationalEvent.event_type == event_type)
            .order_by(OperationalEvent.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def list_events_by_verification_status(
        self,
        status: VerificationStatus,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationalEvent]:
        """
        Retrieve all events in a given verification state.

        Primarily used by the Validation & Enrichment Engine to fetch the
        PENDING queue and by fleet managers to review DISPUTED events.

        Uses the ``ix_operational_events_verification_status`` index.

        Parameters
        ----------
        status : VerificationStatus
            The verification status to filter by (PENDING, VERIFIED, etc.).
        limit : int
            Maximum number of records to return.  Default 50.
        offset : int
            Number of records to skip.  Default 0.

        Returns
        -------
        Sequence[OperationalEvent]
            Matching events ordered by ``occurred_at`` desc.
        """
        stmt = (
            select(OperationalEvent)
            .where(OperationalEvent.verification_status == status)
            .order_by(OperationalEvent.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # Private Helpers
    # -----------------------------------------------------------------------

    async def _get_or_raise(self, event_id: uuid.UUID) -> OperationalEvent:
        """
        Retrieve an event by ID or raise ``EventNotFoundError``.

        Internal helper used by all methods that require the event to exist
        before performing an operation.

        Parameters
        ----------
        event_id : uuid.UUID
            The UUID of the event to retrieve.

        Returns
        -------
        OperationalEvent
            The event instance.

        Raises
        ------
        EventNotFoundError
            If no event with the given UUID exists in the database.
        """
        stmt = select(OperationalEvent).where(OperationalEvent.id == event_id)
        result = await self._db.execute(stmt)
        event: OperationalEvent | None = result.scalar_one_or_none()
        if event is None:
            raise EventNotFoundError(event_id)
        return event
