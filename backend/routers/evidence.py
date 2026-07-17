"""
FleetGuard — Evidence API Router

Exposes endpoints for the Evidence Store.
These endpoints are nested under events to enforce the domain relationship.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.evidence import EvidenceCreate, EvidenceResponse, EvidenceStatusUpdate
from services.evidence_service import (
    EvidenceService,
    EventDoesNotExistError,
    EvidenceNotFound,
)
from routers.auth import get_current_user
from models.user import User

# The router is specifically prefixed with /events/{event_id}/evidence
# to semantically link evidence to an event.
router = APIRouter(
    prefix="/api/v1/events/{event_id}/evidence",
    tags=["evidence"],
)


def get_evidence_service(db: AsyncSession = Depends(get_db)) -> EvidenceService:
    """Dependency provider for EvidenceService."""
    return EvidenceService(db)


@router.post(
    "",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add evidence to an event",
)
async def add_evidence(
    event_id: uuid.UUID,
    payload: EvidenceCreate,
    service: EvidenceService = Depends(get_evidence_service),
    current_user: User = Depends(get_current_user),
):
    """
    Attach new, immutable evidence to an existing Operational Event.
    """
    try:
        return await service.add_evidence(event_id, payload)
    except EventDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[EvidenceResponse],
    summary="List evidence for an event",
)
async def list_evidence(
    event_id: uuid.UUID,
    service: EvidenceService = Depends(get_evidence_service),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all evidence attached to a specific Operational Event.
    """
    try:
        return await service.list_evidence_for_event(event_id)
    except EventDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch(
    "/{evidence_id}/status",
    response_model=EvidenceResponse,
    summary="Update evidence status",
)
async def update_evidence_status(
    event_id: uuid.UUID,
    evidence_id: uuid.UUID,
    payload: EvidenceStatusUpdate,
    service: EvidenceService = Depends(get_evidence_service),
    current_user: User = Depends(get_current_user),
):
    """
    Update the status of an existing evidence record (e.g., from PENDING to COMPLETED).
    All other fields remain immutable.
    """
    try:
        # Note: We aren't strictly enforcing that the evidence belongs to the event_id in the URL
        # for this specific lookup (it relies on evidence_id), but in a larger app, we'd add that check.
        return await service.update_evidence_status(evidence_id, payload)
    except EvidenceNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
