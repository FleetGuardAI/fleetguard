"""
Document Intelligence Framework - Extractors
"""

import abc
import time
from typing import Tuple
from infrastructure.attachments.models import Attachment
from infrastructure.documents.models import ExtractionDiagnostics


class BaseTextExtractor(abc.ABC):
    """
    Abstract strategy for extracting text from an attachment.
    """

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        """Name of the extraction engine"""
        pass

    @abc.abstractmethod
    def extract(self, attachment: Attachment) -> Tuple[str, ExtractionDiagnostics]:
        """
        Extracts text from the attachment.
        Returns a tuple of (extracted_text, diagnostics).
        """
        pass


class MockOCRExtractor(BaseTextExtractor):
    """
    Mock OCR Extractor for testing.
    Simulates text extraction from images.
    """
    @classmethod
    def name(cls) -> str:
        return "MockOCREngine"

    def extract(self, attachment: Attachment) -> Tuple[str, ExtractionDiagnostics]:
        start = time.perf_counter()
        # Mock behavior: return a simple string, perhaps based on the filename or metadata for tests.
        mock_text = attachment.metadata.get("mock_text", "MOCK OCR TEXT")
        
        diagnostics = ExtractionDiagnostics(
            engine=self.name(),
            processing_time_ms=(time.perf_counter() - start) * 1000,
            warnings=[],
            detected_language="en",
            rotation=0
        )
        return mock_text, diagnostics


class MockEmbeddedTextExtractor(BaseTextExtractor):
    """
    Mock Embedded Text Extractor for testing.
    Simulates text extraction directly from PDF/Document bytes.
    """
    @classmethod
    def name(cls) -> str:
        return "MockEmbeddedTextEngine"

    def extract(self, attachment: Attachment) -> Tuple[str, ExtractionDiagnostics]:
        start = time.perf_counter()
        mock_text = attachment.metadata.get("mock_text", "MOCK EMBEDDED TEXT")
        
        diagnostics = ExtractionDiagnostics(
            engine=self.name(),
            processing_time_ms=(time.perf_counter() - start) * 1000,
            warnings=["Fonts not embedded correctly"],
            detected_language="en",
            rotation=None
        )
        return mock_text, diagnostics


def select_extraction_strategy(attachment: Attachment) -> BaseTextExtractor:
    """
    Selects the optimal extraction strategy based on attachment mime_type.
    """
    mime = attachment.mime_type.lower()
    if mime.startswith("image/"):
        return MockOCRExtractor()
    if mime == "application/pdf":
        return MockEmbeddedTextExtractor()
    
    # Default fallback
    return MockOCRExtractor()
