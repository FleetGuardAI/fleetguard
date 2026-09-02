"""
FleetGuard — Evidence Repository

Handles database operations for the Evidence model.
"""

import uuid
from typing import Sequence

from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from models.evidence import Evidence, EvidenceStatus
from models.operational_event import OperationalEvent
from schemas.evidence import EvidenceCreate


class EvidenceNotFoundError(Exception):
    """Raised when an evidence record is not found or does not belong to the tenant."""
    def __init__(self, evidence_id: uuid.UUID) -> None:
        self.evidence_id = evidence_id
        super().__init__(f"Evidence '{evidence_id}' not found.")


class EvidenceRepository:
    """
    CRUD repository for Evidence records.
    Evidence is largely immutable after creation, except for status transitions.
    """
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _verify_event_ownership(self, event_id: uuid.UUID, company_id: int) -> None:
        stmt = select(exists().where(
            OperationalEvent.id == event_id,
            OperationalEvent.company_id == company_id
        ))
        result = await self._session.execute(stmt)
        if not result.scalar():
            raise ValueError(f"OperationalEvent {event_id} not found or unauthorized.")

    async def create(self, event_id: uuid.UUID, company_id: int, payload: EvidenceCreate) -> Evidence:
        """
        Create a new immutable evidence record attached to an Operational Event.
        """
        await self._verify_event_ownership(event_id, company_id)

        evidence = Evidence(
            event_id=event_id,
            evidence_type=payload.evidence_type,
            source=payload.source,
            status=payload.status,
            summary=payload.summary,
            details=payload.details,
            raw_data=payload.raw_data,
        )
        self._session.add(evidence)
        await self._session.flush()
        return evidence

    async def get_by_id(self, evidence_id: uuid.UUID, company_id: int) -> Evidence:
        """
        Retrieve a specific evidence record by ID.
        """
        stmt = (
            select(Evidence)
            .join(OperationalEvent, Evidence.event_id == OperationalEvent.id)
            .where(
                Evidence.id == evidence_id,
                OperationalEvent.company_id == company_id
            )
        )
        result = await self._session.execute(stmt)
        evidence = result.scalar_one_or_none()
        
        if not evidence:
            raise EvidenceNotFoundError(evidence_id)
            
        return evidence

    async def get_for_event(self, event_id: uuid.UUID, company_id: int) -> Sequence[Evidence]:
        """
        Fetch all evidence records attached to a specific Operational Event.
        Ordered chronologically.
        """
        stmt = (
            select(Evidence)
            .join(OperationalEvent, Evidence.event_id == OperationalEvent.id)
            .where(
                Evidence.event_id == event_id,
                OperationalEvent.company_id == company_id
            )
            .order_by(Evidence.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_status(
        self, evidence_id: uuid.UUID, company_id: int, new_status: EvidenceStatus
    ) -> Evidence:
        """
        Update ONLY the status of an evidence record.
        This is typically used for async evidence generation (PENDING -> COMPLETED).
        """
        evidence = await self.get_by_id(evidence_id, company_id)
        evidence.status = new_status
        await self._session.flush()
        return evidence
