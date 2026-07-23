"""
FleetGuard Document Interpretation - Driver License
"""

from typing import List, Any
from domain.document_interpretation.base import BaseDocumentInterpreter
from domain.document_interpretation.models import BusinessDocumentType, ValidationIssue
from domain.document_interpretation.validators import validate_required_fields
from domain.document_interpretation.events import DriverLicenseUpdated
from infrastructure.documents.models import StructuredDocument, DocumentFamily


class DriverLicenseInterpreter(BaseDocumentInterpreter):
    @classmethod
    def key(cls) -> str:
        return "driver_license_interpreter"

    @classmethod
    def get_business_type(cls) -> BusinessDocumentType:
        return BusinessDocumentType.DRIVER_LICENSE

    def supports(self, document: StructuredDocument) -> bool:
        if document.document_family != DocumentFamily.IDENTITY_DOCUMENT:
            return False
            
        text = document.extracted_text.upper()
        if "LICENSE" in text or "LICENCE" in text or "DRIVING" in text:
            return True
            
        return False

    def validate(self, document: StructuredDocument) -> List[ValidationIssue]:
        return validate_required_fields(
            document, 
            ["entity_id"] # Assuming generic identity parser returns entity_id
        )

    def interpret(self, document: StructuredDocument) -> List[Any]:
        field_map = {f.name: f.value for f in document.structured_fields}
        
        license_no = str(field_map.get("entity_id", "UNKNOWN"))
        expiry = str(field_map.get("expiry_date", "2030-01-01"))
        
        event = DriverLicenseUpdated(
            source_document_id=str(document.document_id),
            license_number=license_no,
            expiry_date=expiry
        )
        return [event]
