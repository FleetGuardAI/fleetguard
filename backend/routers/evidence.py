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
from repositories.evidence_repository import EvidenceNotFoundError
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
        return await service.add_evidence(event_id, current_user.company_id, payload)
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
        return await service.list_evidence_for_event(event_id, current_user.company_id)
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
        return await service.update_evidence_status(evidence_id, current_user.company_id, payload)
    except EvidenceNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

@router.get(
    "/{evidence_id}/url",
    response_model=dict,
    summary="Get Signed URL for Evidence",
)
async def get_evidence_url(
    event_id: uuid.UUID,
    evidence_id: uuid.UUID,
    service: EvidenceService = Depends(get_evidence_service),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a short-lived signed URL for an evidence document.
    """
    try:
        # 1. Authorize: Ensure evidence belongs to event, and user can access event.
        try:
            evidence = await service._repo.get_by_id(evidence_id, current_user.company_id)
        except EvidenceNotFoundError:
            raise HTTPException(status_code=404, detail="Evidence not found for this event")
        
        if not evidence or evidence.event_id != event_id:
            raise HTTPException(status_code=404, detail="Evidence not found for this event")
        
        # We need the operational event payload to find the storage path
        from repositories.operational_event_repository import OperationalEventRepository
        
        event_repo = OperationalEventRepository(service._db)
        
        try:
            event = await event_repo.get_event_by_id(event_id, current_user.company_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Note: Event ownership is guaranteed by get_event_by_id(event_id, current_user.company_id)
        
        payload = event.payload or {}
        # UnifiedPipelineService now uses storage_path
        storage_path = payload.get("storage_path") or payload.get("url")
        
        if not storage_path:
            raise HTTPException(status_code=404, detail="No storage path associated with this evidence")
            
        from services.file_upload_service import storage_service
        signed_url = storage_service.create_signed_url(storage_path)
        if not signed_url:
            raise HTTPException(status_code=500, detail="Could not generate signed URL")
            
        return {"signed_url": signed_url}
        
    except EvidenceNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
