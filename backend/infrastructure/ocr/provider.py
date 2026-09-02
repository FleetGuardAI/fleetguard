"""
FleetGuard — OCR Provider Interfaces
"""

import asyncio
import time
import uuid
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional

from infrastructure.ocr.models import OCRResult

logger = logging.getLogger("fleetguard.infrastructure.ocr.provider")


class OCRProvider(ABC):
    """
    Abstract interface for OCR Providers.
    """
    @abstractmethod
    async def extract_text(self, file_data: bytes, mime_type: str, document_type: str = "receipt") -> OCRResult:
        """
        Extract text from a physical document file.
        
        Parameters
        ----------
        file_data : bytes
            The binary content of the document.
        mime_type : str
            The MIME type of the document (e.g., image/jpeg, application/pdf).
        document_type : str
            Type of the document to hint the provider (e.g., "receipt", "idDocument", "invoice").
            
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
    async def extract_text(self, file_data: bytes, mime_type: str, document_type: str = "receipt") -> OCRResult:
        start_time = time.monotonic()
        
        # Simulate network latency (e.g., calling an external API)
        await asyncio.sleep(0.5)
        
        end_time = time.monotonic()
        processing_time_ms = int((end_time - start_time) * 1000)
        
        # Dummy text for testing
        mock_text = f"Extracted mock text for document. Total amount: $150.00."
        
        return OCRResult(
            text=mock_text,
            confidence=0.95,
            provider_name="MockOCRProvider",
            extracted_fields={},
            processing_time_ms=processing_time_ms,
            provider_request_id=str(uuid.uuid4()),
            metadata={"simulated": True, "mime_type": mime_type, "document_type": document_type}
        )


class GoogleDocumentAIProvider(OCRProvider):
    """
    Google Cloud Document AI provider for extracting text and structured fields.
    
    Supports processors in different GCP regions. A separate client is created
    and cached for each region encountered.
    """
    def __init__(self):
        self.project_id = os.environ.get("GOOGLE_DOCUMENT_AI_PROJECT_ID")
        self.default_location = os.environ.get("GOOGLE_DOCUMENT_AI_LOCATION", "us")
        
        # Processor IDs for different document types
        self.receipt_processor = os.environ.get("GOOGLE_DOCUMENT_AI_RECEIPT_PROCESSOR_ID")
        self.receipt_location = os.environ.get("GOOGLE_DOCUMENT_AI_RECEIPT_LOCATION", self.default_location)
        
        self.id_processor = os.environ.get("GOOGLE_DOCUMENT_AI_ID_PROCESSOR_ID")
        self.id_location = os.environ.get("GOOGLE_DOCUMENT_AI_ID_LOCATION", self.default_location)
        
        self.generic_processor = os.environ.get("GOOGLE_DOCUMENT_AI_GENERIC_PROCESSOR_ID")
        self.generic_location = os.environ.get("GOOGLE_DOCUMENT_AI_GENERIC_LOCATION", self.default_location)
        
        if not self.project_id:
            raise ValueError("GOOGLE_DOCUMENT_AI_PROJECT_ID must be set when OCR_PROVIDER is google.")
        
        # Load credentials once — shared across all regional clients
        self._credentials = None
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            import json
            from google.oauth2 import service_account
            try:
                sa_info = json.loads(creds_json)
                self._credentials = service_account.Credentials.from_service_account_info(sa_info)
            except Exception as e:
                logger.error(f"Failed to parse GOOGLE_CREDENTIALS_JSON: {e}")
                raise ValueError(f"Invalid GOOGLE_CREDENTIALS_JSON format: {e}")
        
        # Cache of DocumentProcessorServiceClient instances keyed by region
        self._clients: dict = {}
    
    def _get_client(self, location: str):
        """Return a cached client for the given region, creating one if needed."""
        if location not in self._clients:
            from google.cloud import documentai
            from google.api_core.client_options import ClientOptions
            
            opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
            self._clients[location] = documentai.DocumentProcessorServiceClient(
                client_options=opts, credentials=self._credentials
            )
        return self._clients[location]

    def _get_processor_config(self, document_type: str) -> tuple:
        """Select the appropriate processor ID and region based on document type hint."""
        if document_type == "receipt" and self.receipt_processor:
            return self.receipt_processor, self.receipt_location
        elif document_type in ["idDocument", "driving_license", "aadhaar"] and self.id_processor:
            return self.id_processor, self.id_location
        elif self.generic_processor:
            return self.generic_processor, self.generic_location
        else:
            raise ValueError(f"No configured processor ID available for document type: {document_type}")

    async def extract_text(self, file_data: bytes, mime_type: str, document_type: str = "receipt") -> OCRResult:
        start_time = time.monotonic()
        from google.cloud import documentai
        
        processor_id, location = self._get_processor_config(document_type)
        client = self._get_client(location)
        name = client.processor_path(self.project_id, location, processor_id)
        
        # Enforce Google Document AI limit (typically 20MB for sync requests, we use 15MB to be safe)
        if len(file_data) > 15 * 1024 * 1024:
            raise ValueError("File size exceeds Google Document AI limit (15MB).")
            
        raw_document = documentai.RawDocument(content=file_data, mime_type=mime_type)
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)
        
        try:
            # Document AI Python SDK is currently synchronous, so we run it in an executor thread
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, client.process_document, request)
            
            end_time = time.monotonic()
            processing_time_ms = int((end_time - start_time) * 1000)
            
            document = result.document
            
            # Normalize entities into flat extracted_fields dict
            extracted_fields = {}
            for entity in document.entities:
                # Key maps for backward compatibility with Azure downstream parsers
                key = entity.type_
                
                # Normalize keys for Receipt processor
                if key == "supplier_name":
                    key = "MerchantName"
                elif key == "receipt_date":
                    key = "TransactionDate"
                elif key == "total_amount":
                    key = "Total"
                elif key == "vat_registration_number":
                    key = "MerchantTaxId"
                    
                # Normalize keys for ID Document processor (approximate)
                elif key == "first_name":
                    key = "FirstName"
                elif key == "last_name":
                    key = "LastName"
                elif key == "document_number":
                    key = "DocumentNumber"
                elif key == "date_of_birth":
                    key = "DateOfBirth"
                elif key == "expiration_date":
                    key = "DateOfExpiration"
                    
                val = entity.mention_text
                
                # Resolve normalized values if available (e.g. for dates or amounts)
                if hasattr(entity, 'normalized_value') and entity.normalized_value:
                    if entity.normalized_value.text:
                        val = entity.normalized_value.text
                
                if val:
                    extracted_fields[key] = val
                            
            # Calculate overall confidence
            avg_confidence = 1.0
            if document.entities and len(document.entities) > 0:
                try:
                    avg_confidence = sum(e.confidence for e in document.entities if getattr(e, 'confidence', None) is not None) / len([e for e in document.entities if getattr(e, 'confidence', None) is not None])
                except ZeroDivisionError:
                    avg_confidence = 1.0
                
            return OCRResult(
                text=str(document.text) if document.text else "",
                confidence=avg_confidence,
                provider_name="GoogleDocumentAI",
                extracted_fields=extracted_fields,
                processing_time_ms=processing_time_ms,
                provider_request_id=str(uuid.uuid4()), # Google doesn't easily expose this in standard response
                metadata={"processor_id": processor_id, "mime_type": mime_type}
            )
            
        except Exception as e:
            logger.error(f"Google Document AI extraction failed: {e}")
            raise RuntimeError(f"OCR processing failed: {str(e)}")


def get_ocr_provider() -> OCRProvider:
    provider_type = os.environ.get("OCR_PROVIDER", "mock").lower()
    
    if provider_type == "mock":
        return MockOCRProvider()
    elif provider_type == "google":
        return GoogleDocumentAIProvider()
    else:
        raise ValueError(f"Unknown OCR_PROVIDER configured: {provider_type}")
