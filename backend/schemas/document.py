"""
FleetGuard — Document Schemas

Pydantic models for Document validation and serialization.
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from models.document import DocumentStorageStatus


class DocumentBase(BaseModel):
    """Base fields shared across multiple document schemas."""
    
    original_filename: str = Field(
        ...,
        description="The original name of the uploaded file.",
        examples=["fuel_receipt_102.jpg"],
    )
    mime_type: str = Field(
        ...,
        description="The MIME type of the file.",
        examples=["image/jpeg", "application/pdf"],
    )
    uploaded_by: Optional[str] = Field(
        None,
        description="ID of the user or system that uploaded the document.",
        examples=["user-uuid-123"],
    )


class DocumentCreate(DocumentBase):
    """
    Schema for creating a new Document record in the repository.
    
    Note: The actual file upload is handled via FastAPI's UploadFile,
    this schema represents the metadata extracted from it for DB creation.
    """
    storage_path: str = Field(
        ...,
        description="Location where the physical file is stored.",
        examples=["uploads/uuid-fuel_receipt.jpg"],
    )


class DocumentUpdate(BaseModel):
    """
    Schema for updating an existing Document.
    """
    status: Optional[DocumentStorageStatus] = Field(
        None,
        description="New storage status.",
    )


class DocumentResponse(DocumentBase):
    """
    Schema for returning Document data to clients.
    """
    id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the document.",
    )
    storage_path: str = Field(
        ...,
        description="Location where the physical file is stored.",
    )
    status: DocumentStorageStatus = Field(
        ...,
        description="Current storage status.",
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
