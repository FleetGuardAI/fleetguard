"""
FleetGuard Document Interpretation - Pollution Certificate
"""

from typing import List, Any
from domain.document_interpretation.base import BaseDocumentInterpreter
from domain.document_interpretation.models import BusinessDocumentType, ValidationIssue
from domain.document_interpretation.validators import validate_required_fields
from domain.document_interpretation.events import VehiclePollutionUpdated
from infrastructure.documents.models import StructuredDocument, DocumentFamily


class PollutionCertificateInterpreter(BaseDocumentInterpreter):
    @classmethod
    def key(cls) -> str:
        return "pollution_certificate_interpreter"

    @classmethod
    def get_business_type(cls) -> BusinessDocumentType:
        return BusinessDocumentType.POLLUTION_CERTIFICATE

    def supports(self, document: StructuredDocument) -> bool:
        if document.document_family != DocumentFamily.CERTIFICATE:
            return False
            
        text = document.extracted_text.upper()
        if "POLLUTION" in text or "PUC" in text:
            return True
            
        return False

    def validate(self, document: StructuredDocument) -> List[ValidationIssue]:
        return validate_required_fields(
            document, 
            ["certificate_id", "expiry_date"]
        )

    def interpret(self, document: StructuredDocument) -> List[Any]:
        field_map = {f.name: f.value for f in document.structured_fields}
        
        cert_no = str(field_map.get("certificate_id", "UNKNOWN"))
        expiry = str(field_map.get("expiry_date", "2027-01-01"))
        
        event = VehiclePollutionUpdated(
            source_document_id=str(document.document_id),
            pollution_certificate_number=cert_no,
            expiry_date=expiry
        )
        return [event]
