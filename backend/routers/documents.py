"""
FleetGuard — Document API Router

Exposes endpoints for the Document Ingestion Framework.
Allows clients to upload documents and query their processing status.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import random

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
        return await service.upload_document(file=file, uploaded_by=user_id_str, company_id=current_user.company_id)
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
        return await service.get_document(document_id, company_id=current_user.company_id)
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
        company_id=current_user.company_id,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/ocr/license",
    response_model=Dict[str, Any],
    summary="Mock OCR for Driver License",
)
async def ocr_driver_license(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Mock OCR endpoint that takes an image and returns structured driver license data.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename."
        )

    # Return mocked data for MVP
    valid_until = datetime.now() + timedelta(days=365 * 10)
    
    return {
        "status": "success",
        "data": {
            "name": "Ravi Kumar",
            "license_number": f"UK{random.randint(10, 99)}{random.randint(1000000, 9999999)}",
            "date_of_birth": "1998-04-12",
            "valid_until": valid_until.strftime("%Y-%m-%d"),
            "vehicle_class": "HMV",
        }
    }


@router.post(
    "/ocr/rc",
    response_model=Dict[str, Any],
    summary="Mock OCR for Vehicle RC",
)
async def ocr_vehicle_rc(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Mock OCR endpoint that takes an image and returns structured vehicle RC data.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename."
        )

    # Return mocked data for MVP
    return {
        "status": "success",
        "data": {
            "registration_number": f"UK07AB{random.randint(1000, 9999)}",
            "owner_name": current_user.name,
            "manufacturer": "Tata Motors",
            "model": "Prima",
            "fuel_type": "Diesel",
            "gvw": "55000 kg",
        }
    }
