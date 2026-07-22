"""
Assignment Management Domain - API
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from domain.assignment.models import Assignment, AssignmentStatus
from domain.assignment.schemas import (
    CreateAssignmentRequest,
    UpdateAssignmentRequest,
    AssignmentResponse,
    AssignmentSummaryResponse
)
from domain.assignment.service import AssignmentService
from domain.assignment.queries import AssignmentQueryService
from domain.assignment.repository import InMemoryAssignmentRepository
from domain.assignment.errors import AssignmentDomainError, AssignmentNotFound

router = APIRouter(prefix="/assignments", tags=["assignments"])

# Dependency setup (in reality, provided by a DI container)
_repository = InMemoryAssignmentRepository()
_service = AssignmentService(_repository)
_queries = AssignmentQueryService(_repository)


def get_assignment_service() -> AssignmentService:
    return _service

def get_assignment_queries() -> AssignmentQueryService:
    return _queries


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    request: CreateAssignmentRequest,
    service: AssignmentService = Depends(get_assignment_service)
):
    try:
        assignment = Assignment(
            organization_id=request.organization_id,
            assignment_type=request.assignment_type,
            source_entity_id=request.source_entity_id,
            target_entity_id=request.target_entity_id,
            created_by=request.created_by,
            metadata=request.metadata
        )
        if request.effective_from:
            # Reconstruct with the provided date
            assignment = assignment.model_copy(update={"effective_from": request.effective_from})
            
        created = service.create_assignment(assignment)
        return created
    except AssignmentDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[AssignmentSummaryResponse])
def list_assignments(
    organization_id: Optional[uuid.UUID] = None,
    queries: AssignmentQueryService = Depends(get_assignment_queries)
):
    # Returns history. A fully featured API would paginate and filter
    summaries = queries.assignment_history()
    return summaries


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: uuid.UUID,
    service: AssignmentService = Depends(get_assignment_service)
):
    try:
        return service._get_assignment(assignment_id)
    except AssignmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


class ReasonRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/{assignment_id}/activate", response_model=AssignmentResponse)
def activate_assignment(
    assignment_id: uuid.UUID,
    request: ReasonRequest,
    service: AssignmentService = Depends(get_assignment_service)
):
    try:
        return service.activate_assignment(assignment_id, request.reason)
    except AssignmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AssignmentDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{assignment_id}/suspend", response_model=AssignmentResponse)
def suspend_assignment(
    assignment_id: uuid.UUID,
    request: ReasonRequest,
    service: AssignmentService = Depends(get_assignment_service)
):
    try:
        return service.suspend_assignment(assignment_id, request.reason)
    except AssignmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AssignmentDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{assignment_id}/end", response_model=AssignmentResponse)
def end_assignment(
    assignment_id: uuid.UUID,
    request: ReasonRequest,
    service: AssignmentService = Depends(get_assignment_service)
):
    try:
        return service.end_assignment(assignment_id, request.reason)
    except AssignmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AssignmentDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


class TransferRequest(BaseModel):
    new_target_entity_id: str
    reason: Optional[str] = None


@router.post("/{assignment_id}/transfer", response_model=AssignmentResponse)
def transfer_assignment(
    assignment_id: uuid.UUID,
    request: TransferRequest,
    service: AssignmentService = Depends(get_assignment_service)
):
    try:
        return service.transfer_assignment(assignment_id, request.new_target_entity_id, request.reason)
    except AssignmentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AssignmentDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))
