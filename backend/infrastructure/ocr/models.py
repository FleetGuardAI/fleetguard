"""
FleetGuard — OCR Infrastructure Models
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    """
    Standardized output from any OCR Provider.
    """
    text: str = Field(..., description="The raw extracted text from the document.")
    confidence: float = Field(..., description="Overall confidence score of the extraction (0.0 to 1.0).")
    provider_name: str = Field(..., description="The name of the OCR provider used (e.g., 'MockOCRProvider', 'AzureDocumentIntelligence').")
    
    # Extended Operational Metadata
    processing_time_ms: int = Field(..., description="Time taken to process the document in milliseconds.")
    provider_request_id: Optional[str] = Field(None, description="A unique tracking ID from the external provider.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Any additional provider-specific context.")
