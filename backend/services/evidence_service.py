"""
FleetGuard — Evidence Service

Handles business logic for the Evidence store.
Ensures Operational Events exist before attaching Evidence.
"""

import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.evidence_repository import EvidenceRepository, EvidenceNotFoundError
from repositories.operational_event_repository import OperationalEventRepository, EventNotFoundError
from schemas.evidence import EvidenceCreate, EvidenceResponse, EvidenceStatusUpdate


class EvidenceServiceError(Exception):
    """Base exception for evidence service errors."""
    pass


class EventDoesNotExistError(EvidenceServiceError):
    """Raised when trying to attach evidence to a non-existent event."""
    def __init__(self, event_id: uuid.UUID) -> None:
        self.event_id = event_id
        super().__init__(f"Operational Event '{event_id}' not found.")


class EvidenceNotFound(EvidenceServiceError):
    """Raised when evidence is not found."""
    def __init__(self, evidence_id: uuid.UUID) -> None:
        self.evidence_id = evidence_id
        super().__init__(f"Evidence '{evidence_id}' not found.")


class EvidenceService:
    """
    Coordinates evidence attachment to events.
    """
    
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = EvidenceRepository(db)
        self._event_repo = OperationalEventRepository(db)

    async def add_evidence(
        self,
        event_id: uuid.UUID,
        payload: EvidenceCreate,
    ) -> EvidenceResponse:
        """
        Validate that the event exists, then create the evidence record.
        """
        try:
            # Check if event exists. The repository raises EventNotFoundError if it doesn't.
            await self._event_repo.get_event_by_id(event_id)
        except EventNotFoundError:
            raise EventDoesNotExistError(event_id)
            
        evidence = await self._repo.create(event_id, payload)
        return EvidenceResponse.model_validate(evidence)

    async def get_evidence(self, evidence_id: uuid.UUID) -> EvidenceResponse:
        """
        Retrieve a specific evidence record by ID.
        """
        try:
            evidence = await self._repo.get_by_id(evidence_id)
            return EvidenceResponse.model_validate(evidence)
        except EvidenceNotFoundError:
            raise EvidenceNotFound(evidence_id)

    async def list_evidence_for_event(
        self,
        event_id: uuid.UUID,
    ) -> list[EvidenceResponse]:
        """
        List all evidence attached to a specific event.
        Also validates that the event exists.
        """
        try:
            await self._event_repo.get_event_by_id(event_id)
        except EventNotFoundError:
            raise EventDoesNotExistError(event_id)
            
        evidence_list = await self._repo.get_for_event(event_id)
        return [EvidenceResponse.model_validate(ev) for ev in evidence_list]

    async def update_evidence_status(
        self,
        evidence_id: uuid.UUID,
        payload: EvidenceStatusUpdate,
    ) -> EvidenceResponse:
        """
        Update the status of an existing async evidence request.
        """
        try:
            evidence = await self._repo.update_status(evidence_id, payload.status)
            return EvidenceResponse.model_validate(evidence)
        except EvidenceNotFoundError:
            raise EvidenceNotFound(evidence_id)
