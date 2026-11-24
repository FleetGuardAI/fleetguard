"""
FleetGuard — Document Repository

Handles all database operations for the Document model.
Isolates SQLAlchemy 2.x async queries from the Service layer.
"""

import uuid
from typing import Sequence, Optional

from sqlalchemy import select, update, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.document import Document, DocumentStorageStatus
from schemas.document import DocumentCreate, DocumentUpdate


class DocumentNotFoundError(Exception):
    """Raised when a document is not found by ID."""
    def __init__(self, document_id: uuid.UUID) -> None:
        self.document_id = document_id
        super().__init__(f"Document '{document_id}' not found.")


class DocumentRepository:
    """
    CRUD repository for the Document model.
    """
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, payload: DocumentCreate) -> Document:
        """
        Create a new Document record.
        """
        doc = Document(
            original_filename=payload.original_filename,
            mime_type=payload.mime_type,
            storage_path=payload.storage_path,
            uploaded_by=payload.uploaded_by,
            company_id=payload.company_id,
            name=payload.name,
            category=payload.category,
            expiry_date=payload.expiry_date,
            target_id=payload.target_id,
            target_type=payload.target_type,
        )
        self._session.add(doc)
        await self._session.flush()
        return doc

    async def get_by_id(self, document_id: uuid.UUID, company_id: Optional[int] = None) -> Document:
        """
        Retrieve a document by its UUID.
        Raises DocumentNotFoundError if not found.
        """
        stmt = select(Document).where(Document.id == document_id)
        if company_id is not None:
            stmt = stmt.where(Document.company_id == company_id)
            
        result = await self._session.execute(stmt)
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise DocumentNotFoundError(document_id)
            
        return doc

    async def list_documents(
        self,
        *,
        status: Optional[DocumentStorageStatus] = None,
        company_id: Optional[int] = None,
        driver_user_id: Optional[str] = None,
        driver_target_ids: Optional[Sequence[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[Document]:
        """
        List documents, optionally filtered by status, company_id, and driver scoping.
        Ordered by creation time descending.
        """
        stmt = select(Document).order_by(Document.created_at.desc())
        
        if status:
            stmt = stmt.where(Document.status == status)
            
        if company_id is not None:
            stmt = stmt.where(Document.company_id == company_id)

        # FG-SEC-028: Enforce horizontal IDOR protection for drivers
        if driver_user_id is not None:
            target_ids = list(driver_target_ids or [])
            if target_ids:
                stmt = stmt.where(
                    or_(
                        Document.uploaded_by == driver_user_id,
                        and_(
                            Document.target_type == "driver",
                            Document.target_id.in_(target_ids)
                        )
                    )
                )
            else:
                stmt = stmt.where(Document.uploaded_by == driver_user_id)
            
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update(self, document_id: uuid.UUID, payload: DocumentUpdate, company_id: Optional[int] = None) -> Document:
        """
        Update an existing document status.
        """
        doc = await self.get_by_id(document_id, company_id=company_id)
        
        if payload.status is not None:
            doc.status = payload.status
            
        await self._session.flush()
        await self._session.refresh(doc)
        return doc
