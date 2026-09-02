"""
FleetGuard — Unified Document Pipeline Service

Handles the complete lifecycle of document ingestion:
1. Upload file and permanent storage
2. Create Document DB record
3. Trigger OCR via Google Document AI
4. Save Evidence and OperationalEvent
5. Extract expiry dates and structured fields
"""

import logging
from datetime import datetime, timezone
from dateutil import parser
from typing import Optional, Dict, Any, Tuple
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from models.document import DocumentStorageStatus
from services.document_service import DocumentService
from infrastructure.ocr.provider import get_ocr_provider
from models.operational_event import OperationalEvent, EventType, EntityType, CaptureMethod
from models.evidence import Evidence, EvidenceType, EvidenceStatus
from models.driver_domain import Driver
from models.vehicle_domain import Vehicle

logger = logging.getLogger("fleetguard.unified_pipeline")


class UnifiedPipelineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.document_service = DocumentService(db)

    async def process_document(
        self,
        file: UploadFile,
        document_type: str,
        entity_type: EntityType,
        entity_id: str,
        uploaded_by: str,
        company_id: Optional[int] = None,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Process a document upload through the unified pipeline.
        Returns the stored URL and extracted fields (if OCR succeeded).
        """
        # Step 1 & 2: Upload and Create Document Record
        try:
            doc_response = await self.document_service.upload_document(
                file=file,
                uploaded_by=uploaded_by,
                company_id=company_id
            )
            url = doc_response.storage_path
            doc_id = doc_response.id
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            raise RuntimeError(f"Document upload failed: {e}")

        # Step 3: Trigger OCR
        content = await file.read()
        await file.seek(0)
        provider = get_ocr_provider()
        
        extracted_fields = None
        ocr_failed = False
        ocr_error = None
        ocr_result = None

        try:
            ocr_result = await provider.extract_text(
                file_data=content,
                mime_type=file.content_type or "image/jpeg",
                document_type=document_type
            )
            extracted_fields = ocr_result.extracted_fields
        except Exception as e:
            logger.error(f"OCR processing failed for {url}: {e}")
            ocr_failed = True
            ocr_error = str(e)
            # DO NOT fail the upload. Mark Document as FAILED OCR but keep it.
            await self.document_service.update_document_status(doc_id, DocumentStorageStatus.FAILED, company_id)

        # Step 4: Save Evidence and OperationalEvent
        event = OperationalEvent(
            event_type=EventType.DOCUMENT_UPLOADED,
            entity_type=entity_type,
            entity_id=entity_id,
            occurred_at=datetime.now(timezone.utc),
            capture_method=CaptureMethod.SYSTEM_GENERATED,
            created_by=uploaded_by,
            payload={"url": url, "filename": file.filename, "document_type": document_type}
        )
        self.db.add(event)
        await self.db.flush()

        if ocr_result and not ocr_failed:
            evidence = Evidence(
                event_id=event.id,
                evidence_type=EvidenceType.OCR_EXTRACTION,
                source=ocr_result.provider_name,
                status=EvidenceStatus.COMPLETED,
                summary=f"Extracted {len(extracted_fields)} fields",
                details=ocr_result.text[:500] if ocr_result.text else None,
                raw_data={
                    "extracted_fields": extracted_fields,
                    "confidence": ocr_result.confidence,
                    "processing_time_ms": ocr_result.processing_time_ms,
                    "provider_request_id": ocr_result.provider_request_id,
                    "metadata": ocr_result.metadata
                }
            )
            self.db.add(evidence)
            
            # Update Document status to AVAILABLE since OCR succeeded
            await self.document_service.update_document_status(doc_id, DocumentStorageStatus.AVAILABLE, company_id)

        await self.db.commit()

        # Step 5: Extract Expiry Data and update models
        if extracted_fields:
            await self._update_entity_expiry(entity_type, entity_id, document_type, extracted_fields)

        return url, extracted_fields

    async def _update_entity_expiry(self, entity_type: EntityType, entity_id: str, document_type: str, fields: Dict[str, Any]):
        """Update Expiry dates on domain models based on OCR extraction."""
        expiry_str = fields.get("DateOfExpiration") or fields.get("ExpiryDate")
        if not expiry_str:
            return

        try:
            # Safely parse date
            expiry_date = parser.parse(str(expiry_str)).date()
        except Exception as e:
            logger.warning(f"Could not parse expiry date '{expiry_str}': {e}")
            return

        if entity_type == EntityType.DRIVER:
            if document_type in ["driving_license", "license_front", "license"]:
                from sqlalchemy import select
                result = await self.db.execute(select(Driver).where(Driver.id == int(entity_id)))
                driver = result.scalar_one_or_none()
                if driver:
                    driver.license_valid_until = expiry_date
                    await self.db.commit()

        elif entity_type == EntityType.VEHICLE:
            from sqlalchemy import select
            try:
                vid = int(entity_id)
                result = await self.db.execute(select(Vehicle).where(Vehicle.id == vid))
                vehicle = result.scalar_one_or_none()
                if vehicle:
                    if document_type == "insurance":
                        vehicle.insurance_expiry = expiry_date
                    elif document_type == "puc":
                        vehicle.puc_expiry = expiry_date
                    elif document_type == "fitness_certificate":
                        vehicle.fitness_expiry = expiry_date
                    elif document_type == "permit":
                        vehicle.permit_expiry = expiry_date
                    await self.db.commit()
            except ValueError:
                logger.warning(f"Invalid vehicle ID format: {entity_id}")
