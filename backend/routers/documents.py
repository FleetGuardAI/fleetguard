"""
FleetGuard — Document API Router

Exposes endpoints for the Document Ingestion Framework.
Allows clients to upload documents and query their processing status.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.document import DocumentStorageStatus
from schemas.document import DocumentResponse
from services.document_service import DocumentService, DocumentNotFound
from routers.auth import get_current_user
from models.user import User

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["documents"],
)


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Dependency provider for DocumentService."""
    return DocumentService(db)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new document",
)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a physical document to the ingestion pipeline.
    The file is stored securely and queued for processing.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename."
        )

    # Convert UUID to string for the uploaded_by field
    user_id_str = str(current_user.id)
    
    try:
        return await service.upload_document(file=file, uploaded_by=user_id_str)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document by ID",
)
async def get_document(
    document_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the metadata and processing status of a specific document.
    """
    try:
        return await service.get_document(document_id)
    except DocumentNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[DocumentResponse],
    summary="List uploaded documents",
)
async def list_documents(
    storage_status: Optional[DocumentStorageStatus] = None,
    limit: int = 50,
    offset: int = 0,
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    """
    List documents with optional filtering by storage status.
    """
    return await service.list_documents(
        status=storage_status,
        limit=limit,
        offset=offset,
    )
