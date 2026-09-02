"""
FleetGuard — Document Service

Handles business logic for document ingestion, including saving physical
files to storage (local disk for now) and coordinating with the repository.
"""

import os
import uuid
import shutil
from typing import Sequence, Optional
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from models.document import DocumentStorageStatus
from repositories.document_repository import DocumentRepository, DocumentNotFoundError
from schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate


# Define upload directory (relative to backend root)


class DocumentServiceError(Exception):
    """Base exception for document service errors."""
    pass


class DocumentNotFound(DocumentServiceError):
    """Raised when a document is not found."""
    def __init__(self, document_id: uuid.UUID) -> None:
        self.document_id = document_id
        super().__init__(f"Document '{document_id}' not found.")


class DocumentService:
    """
    Coordinates document uploads, storage, and retrieval.
    """
    
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = DocumentRepository(db)
        
        # Ensure upload directory exists

    async def upload_document(
        self,
        file: UploadFile,
        uploaded_by: Optional[str] = None,
        company_id: Optional[int] = None,
        name: Optional[str] = None,
        category: Optional[str] = None,
        expiry_date: Optional[str] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
    ) -> DocumentResponse:
        """
        Save the uploaded file to disk and create a Document record.
        """
        # Generate a unique filename to prevent collisions
        file_ext = ""
        if file.filename and "." in file.filename:
            file_ext = "." + file.filename.split(".")[-1]
            
        document_id = uuid.uuid4()
        storage_filename = f"{document_id}{file_ext}"
        
        from services.file_upload_service import storage_service
        from fastapi import HTTPException
        try:
            storage_path = await storage_service.upload_file(
                file=file,
                folder="documents",
                filename=storage_filename
            )
        except HTTPException:
            raise
        except Exception as e:
            raise DocumentServiceError(f"Failed to upload document to storage: {e}")
            
        # Create DB record
        create_schema = DocumentCreate(
            original_filename=file.filename or "unknown",
            mime_type=file.content_type or "application/octet-stream",
            storage_path=storage_path,
            uploaded_by=uploaded_by,
            company_id=company_id,
            name=name,
            category=category,
            expiry_date=expiry_date,
            target_id=target_id,
            target_type=target_type
        )
        
        try:
            doc = await self._repo.create(create_schema)
            resp = DocumentResponse.model_validate(doc)
            resp.storage_path = storage_service.create_signed_url(doc.storage_path)
            return resp
        except Exception as e:
            # Cleanup if DB fails
            await storage_service.delete_file(storage_path)
            raise DocumentServiceError(f"Failed to save document record: {e}")

    async def get_document(self, document_id: uuid.UUID, company_id: Optional[int] = None) -> DocumentResponse:
        """Retrieve a document by ID."""
        try:
            doc = await self._repo.get_by_id(document_id, company_id=company_id)
            resp = DocumentResponse.model_validate(doc)
            from services.file_upload_service import storage_service
            resp.storage_path = storage_service.create_signed_url(doc.storage_path)
            return resp
        except DocumentNotFoundError:
            raise DocumentNotFound(document_id)

    async def list_documents(
        self,
        *,
        status: Optional[DocumentStorageStatus] = None,
        company_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[DocumentResponse]:
        """List documents, optionally filtered by status and company."""
        docs = await self._repo.list_documents(
            status=status,
            company_id=company_id,
            limit=limit,
            offset=offset
        )
        from services.file_upload_service import storage_service
        results = []
        for doc in docs:
            resp = DocumentResponse.model_validate(doc)
            resp.storage_path = storage_service.create_signed_url(doc.storage_path)
            results.append(resp)
        return results

    async def update_document_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStorageStatus,
        company_id: Optional[int] = None
    ) -> DocumentResponse:
        """Update the storage status of a document."""
        update_schema = DocumentUpdate(status=status)
        try:
            doc = await self._repo.update(document_id, update_schema, company_id=company_id)
            resp = DocumentResponse.model_validate(doc)
            from services.file_upload_service import storage_service
            resp.storage_path = storage_service.create_signed_url(doc.storage_path)
            return resp
        except DocumentNotFoundError:
            raise DocumentNotFound(document_id)
