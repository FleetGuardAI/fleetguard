"""
Document Intelligence Framework - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class DocumentFamily(str, Enum):
    """
    Generic Document Families, irrespective of FleetGuard specific business logic.
    """
    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"
    CERTIFICATE = "CERTIFICATE"
    IDENTITY_DOCUMENT = "IDENTITY_DOCUMENT"
    FORM = "FORM"
    UNKNOWN = "UNKNOWN"


class ExtractedField(BaseModel):
    """
    Immutable representation of an individual structured field parsed from a document.
    """
    name: str
    value: Any
    confidence: Optional[float] = None
    source_info: Optional[str] = None
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class ExtractionDiagnostics(BaseModel):
    """
    Metadata describing the extraction execution.
    """
    engine: str
    processing_time_ms: float
    warnings: List[str] = Field(default_factory=list)
    detected_language: Optional[str] = None
    rotation: Optional[int] = None
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class StructuredDocument(BaseModel):
    """
    Immutable representation of a document that has been successfully extracted, classified, and parsed.
    """
    document_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    attachment_id: str
    document_family: DocumentFamily
    extraction_method: str
    extracted_text: str
    structured_fields: List[ExtractedField] = Field(default_factory=list)
    diagnostics: Optional[ExtractionDiagnostics] = None
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class DocumentProcessingStatus(str, Enum):
    """
    Status of the document through the intelligence pipeline.
    """
    SUCCESS = "SUCCESS"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    CLASSIFICATION_FAILED = "CLASSIFICATION_FAILED"
    PARSING_FAILED = "PARSING_FAILED"
    UNKNOWN_TYPE = "UNKNOWN_TYPE"


class DocumentProcessingResult(BaseModel):
    """
    Wrapper returning the result of document processing.
    """
    structured_document: Optional[StructuredDocument] = None
    processing_status: DocumentProcessingStatus
    error_message: Optional[str] = None
    execution_time: float
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
