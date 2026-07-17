"""
FleetGuard — OCR Provider Interfaces
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod

from infrastructure.ocr.models import OCRResult


class OCRProvider(ABC):
    """
    Abstract interface for OCR Providers.
    """
    @abstractmethod
    async def extract_text(self, file_path: str, mime_type: str) -> OCRResult:
        """
        Extract text from a physical document file.
        
        Parameters
        ----------
        file_path : str
            The local file path or URI to the document.
        mime_type : str
            The MIME type of the document (e.g., image/jpeg, application/pdf).
            
        Returns
        -------
        OCRResult
            The standardized OCR extraction result.
        """
        pass


class MockOCRProvider(OCRProvider):
    """
    A dummy OCR provider for local testing and development.
    It simulates a network delay and returns generic extracted text.
    """
    async def extract_text(self, file_path: str, mime_type: str) -> OCRResult:
        start_time = time.monotonic()
        
        # Simulate network latency (e.g., calling an external API)
        await asyncio.sleep(0.5)
        
        end_time = time.monotonic()
        processing_time_ms = int((end_time - start_time) * 1000)
        
        # Dummy text for testing
        mock_text = f"Extracted mock text for document at {file_path}. Total amount: $150.00."
        
        return OCRResult(
            text=mock_text,
            confidence=0.95,
            provider_name="MockOCRProvider",
            processing_time_ms=processing_time_ms,
            provider_request_id=str(uuid.uuid4()),
            metadata={"simulated": True, "mime_type": mime_type}
        )
