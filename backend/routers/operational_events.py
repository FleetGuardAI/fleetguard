"""
FleetGuard — Operational Event Router

Exposes the Operational Event Service through REST endpoints.

This router is intentionally thin.

Responsibilities
----------------
• Validate incoming request data (handled by Pydantic / FastAPI automatically).
• Construct the service and call the appropriate method.
• Map service exceptions to HTTP status codes.
• Return the correct Pydantic response schema.

This router does NOT:
• Access the database or repository directly.
• Contain business logic.
• Verify event payloads.
• Dispatch events.
• Update Digital Twins or Fleet Memory.

URL Prefix
----------
All endpoints are mounted at ``/api/v1/events``.

Endpoints
---------
POST   /api/v1/events                                    Submit a new event
GET    /api/v1/events                                    List events (paginated)
GET    /api/v1/events/{event_id}                         Get single event by UUID
GET    /api/v1/events/entity/{entity_type}/{entity_id}   Events for a specific entity
GET    /api/v1/events/type/{event_type}                  Events by event type
GET    /api/v1/events/status/{verification_status}       Events by verification status
PATCH  /api/v1/events/{event_id}/notes                   Update annotation
PATCH  /api/v1/events/{event_id}/metadata                Update event metadata

Exception Mapping
-----------------
EventNotFound   → HTTP 404
EventWriteError → HTTP 500
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, get_uow
from models.operational_event import EntityType, EventType, VerificationStatus
from schemas.operational_event import (
    OperationalEventCreate,
    OperationalEventResponse,
    OperationalEventUpdate,
)
from services.operational_event_service import (
    EventNotFound,
    EventWriteError,
    OperationalEventService,
)

router = APIRouter(
    prefix="/api/v1/events",
    tags=["Operational Events"],
)


# ---------------------------------------------------------------------------
# Dependency — service factory
# ---------------------------------------------------------------------------

def get_event_service(
    uow = Depends(get_uow),
) -> OperationalEventService:
    """
    FastAPI dependency that constructs an ``OperationalEventService``.

    Inject with ``Depends(get_event_service)`` in endpoint signatures.
    """
    return OperationalEventService(uow)


# ---------------------------------------------------------------------------
# PATCH schemas (inline — narrow request bodies for update endpoints)
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field


class NotesUpdateRequest(BaseModel):
    """Request body for PATCH /events/{event_id}/notes."""

    notes: str | None = Field(
        None,
        description="Free-text annotation. Pass null to clear the notes field.",
        examples=["Reviewed and confirmed by fleet manager."],
    )


class MetadataUpdateRequest(BaseModel):
    """Request body for PATCH /events/{event_id}/metadata."""

    event_metadata: dict[str, Any] = Field(
        ...,
        description=(
            "Operational metadata to associate with the event. "
            "Replaces the existing metadata entirely."
        ),
        examples=[{"enriched_by": "validation_engine_v1", "processed_at": "2026-07-14T10:00:00Z"}],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _handle_service_error(exc: Exception, event_id: uuid.UUID | None = None) -> None:
    """
    Translate service-layer exceptions into appropriate HTTP responses.

    Called at the bottom of every except block in this router.
    """
    if isinstance(exc, EventNotFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operational event '{exc.event_id}' not found.",
        )
    if isinstance(exc, EventWriteError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Event write error: {exc.detail}",
        )
    # Unexpected — re-raise so FastAPI's default handler logs it
    raise exc


# ---------------------------------------------------------------------------
# POST /api/v1/events
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=OperationalEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new Operational Event",
    description=(
        "Record a new fleet Operational Event. "
        "The event is stored immediately with PENDING verification status. "
        "Future milestones will wire dispatch and validation automatically."
    ),
)
async def create_event(
    payload: OperationalEventCreate,
    service: OperationalEventService = Depends(get_event_service),
) -> OperationalEventResponse:
    """Submit a new fleet Operational Event."""
    try:
        return await service.create_event(payload)
    except (EventNotFound, EventWriteError) as exc:
        _handle_service_error(exc)


# ---------------------------------------------------------------------------
# GET /api/v1/events
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[OperationalEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Operational Events",
    description="Return a paginated list of all events, ordered by occurred_at descending.",
)
async def list_events(
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum records to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Records to skip.")] = 0,
    service: OperationalEventService = Depends(get_event_service),
) -> list[OperationalEventResponse]:
    """List all Operational Events with pagination."""
    events = await service.list_events(limit=limit, offset=offset)
    return list(events)


# ---------------------------------------------------------------------------
# GET /api/v1/events/entity/{entity_type}/{entity_id}
#
# NOTE: Static-prefix routes (/entity/, /type/, /status/) are defined BEFORE
# the parameterised /{event_id} route so FastAPI does not mistake them for UUID
# path parameters.
# ---------------------------------------------------------------------------

@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=list[OperationalEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Events for a Specific Entity",
    description=(
        "Return all events for a given fleet entity (e.g. vehicle MH12AB1234). "
        "Uses the composite (entity_type, entity_id) index."
    ),
)
async def list_events_by_entity(
    entity_type: EntityType,
    entity_id: str,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: OperationalEventService = Depends(get_event_service),
) -> list[OperationalEventResponse]:
    """List all events for a specific fleet entity."""
    events = await service.list_events_by_entity(
        entity_type, entity_id, limit=limit, offset=offset
    )
    return list(events)


# ---------------------------------------------------------------------------
# GET /api/v1/events/type/{event_type}
# ---------------------------------------------------------------------------

@router.get(
    "/type/{event_type}",
    response_model=list[OperationalEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Events by Event Type",
    description="Return all events of a given EventType (e.g. FUEL_FILLED).",
)
async def list_events_by_type(
    event_type: EventType,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: OperationalEventService = Depends(get_event_service),
) -> list[OperationalEventResponse]:
    """List all events of a specific EventType."""
    events = await service.list_events_by_type(event_type, limit=limit, offset=offset)
    return list(events)


# ---------------------------------------------------------------------------
# GET /api/v1/events/status/{verification_status}
# ---------------------------------------------------------------------------

@router.get(
    "/status/{verification_status}",
    response_model=list[OperationalEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Events by Verification Status",
    description=(
        "Return all events in a given verification state "
        "(PENDING, VERIFIED, DISPUTED, REJECTED)."
    ),
)
async def list_events_by_status(
    verification_status: VerificationStatus,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: OperationalEventService = Depends(get_event_service),
) -> list[OperationalEventResponse]:
    """List all events in a specific VerificationStatus state."""
    events = await service.list_events_by_verification_status(
        verification_status, limit=limit, offset=offset
    )
    return list(events)


# ---------------------------------------------------------------------------
# GET /api/v1/events/{event_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{event_id}",
    response_model=OperationalEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a Single Operational Event",
    description="Retrieve a single Operational Event by its UUID.",
)
async def get_event(
    event_id: uuid.UUID,
    service: OperationalEventService = Depends(get_event_service),
) -> OperationalEventResponse:
    """Retrieve a single Operational Event by UUID."""
    try:
        return await service.get_event(event_id)
    except EventNotFound as exc:
        _handle_service_error(exc)


# ---------------------------------------------------------------------------
# PATCH /api/v1/events/{event_id}/notes
# ---------------------------------------------------------------------------

@router.patch(
    "/{event_id}/notes",
    response_model=OperationalEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Event Notes",
    description=(
        "Update the free-text annotation of an existing event. "
        "Pass null to clear the notes field."
    ),
)
async def update_event_notes(
    event_id: uuid.UUID,
    payload: NotesUpdateRequest,
    service: OperationalEventService = Depends(get_event_service),
) -> OperationalEventResponse:
    """Update the notes annotation of an Operational Event."""
    try:
        return await service.update_notes(event_id, payload.notes)
    except (EventNotFound, EventWriteError) as exc:
        _handle_service_error(exc)


# ---------------------------------------------------------------------------
# PATCH /api/v1/events/{event_id}/metadata
# ---------------------------------------------------------------------------

@router.patch(
    "/{event_id}/metadata",
    response_model=OperationalEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Event Metadata",
    description=(
        "Replace the event_metadata JSONB field of an existing event. "
        "Intended for the Validation & Enrichment Engine to annotate "
        "events with processing context."
    ),
)
async def update_event_metadata(
    event_id: uuid.UUID,
    payload: MetadataUpdateRequest,
    service: OperationalEventService = Depends(get_event_service),
) -> OperationalEventResponse:
    """Replace the event_metadata of an Operational Event."""
    try:
        return await service.update_metadata(event_id, payload.event_metadata)
    except (EventNotFound, EventWriteError) as exc:
        _handle_service_error(exc)
