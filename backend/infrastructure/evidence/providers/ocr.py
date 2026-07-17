"""
FleetGuard — OCR Evidence Provider
"""

import logging
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.ocr.provider import OCRProvider
from repositories.document_repository import DocumentRepository, DocumentNotFoundError
from schemas.operational_event import OperationalEventResponse

from infrastructure.evidence.provider import BaseEvidenceProvider
from schemas.evidence_sdk import EvidenceRequest, EvidenceResult, ProviderStatus
from models.evidence import EvidenceType

logger = logging.getLogger("fleetguard.infrastructure.evidence.ocr")


class OCREvidenceProvider(BaseEvidenceProvider):
    """
    Extracts OCR data from a document and creates an Evidence record.
    Acts as a provider within the Evidence Framework.
    """
    def __init__(
        self,
        db_session_factory,
        provider: OCRProvider,
    ) -> None:
        self._db_session_factory = db_session_factory
        self._provider = provider

    @property
    def name(self) -> str:
        return "ocr_provider"

    async def applies_to(self, request: EvidenceRequest) -> bool:
        """
        Applies if the event payload contains a 'document_id'.
        """
        payload = request.event.payload or {}
        return "document_id" in payload

    async def collect(self, request: EvidenceRequest) -> EvidenceResult:
        """
        Reads a document, runs OCR, and returns raw evidence data.
        """
        payload = request.event.payload or {}
        document_id_str = payload.get("document_id")
        if not document_id_str:
            return EvidenceResult(
                status=ProviderStatus.FAILED, 
                provider_name=self.name,
                evidence_type=EvidenceType.OCR_EXTRACTION,
                errors=["No document_id in payload"]
            )
            
        try:
            document_id = uuid.UUID(document_id_str)
        except ValueError:
            return EvidenceResult(
                status=ProviderStatus.FAILED, 
                provider_name=self.name,
                evidence_type=EvidenceType.OCR_EXTRACTION,
                errors=[f"Invalid document_id: {document_id_str}"]
            )

        async with self._db_session_factory() as db:
            doc_repo = DocumentRepository(db)
            
            try:
                doc = await doc_repo.get_by_id(document_id)
            except DocumentNotFoundError:
                logger.error(f"Cannot process OCR: Document {document_id} not found.")
                return EvidenceResult(
                    status=ProviderStatus.FAILED, 
                    provider_name=self.name,
                    evidence_type=EvidenceType.OCR_EXTRACTION,
                    errors=[f"Document {document_id} not found"]
                )
                
            logger.info(f"Starting OCR evidence extraction for Document {document_id} (Event: {request.event.id})")

            try:
                # Execute the OCR extraction
                result = await self._provider.extract_text(doc.storage_path, doc.mime_type)
                
                logger.info(f"Successfully ran OCR extraction for Document {document_id}")
                return EvidenceResult(
                    status=ProviderStatus.COMPLETED, 
                    provider_name=self.name,
                    evidence_type=EvidenceType.OCR_EXTRACTION,
                    summary=f"Extracted {len(result.text)} characters.",
                    details=f"Confidence: {result.confidence}",
                    raw_data=result.model_dump(),
                    confidence=result.confidence
                )
                
            except Exception as e:
                logger.exception(f"OCR extraction failed for Document {document_id}: {e}")
                
                return EvidenceResult(
                    status=ProviderStatus.FAILED, 
                    provider_name=self.name,
                    evidence_type=EvidenceType.OCR_EXTRACTION,
                    errors=[str(e)]
                )
