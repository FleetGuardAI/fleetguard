"""
FleetGuard Document Interpretation - Registration Certificate
"""

from typing import List, Any
from domain.document_interpretation.base import BaseDocumentInterpreter
from domain.document_interpretation.models import BusinessDocumentType, ValidationIssue
from domain.document_interpretation.validators import validate_required_fields
from domain.document_interpretation.events import VehicleRegistrationUpdated
from infrastructure.documents.models import StructuredDocument, DocumentFamily


class RegistrationCertificateInterpreter(BaseDocumentInterpreter):
    @classmethod
    def key(cls) -> str:
        return "registration_certificate_interpreter"

    @classmethod
    def get_business_type(cls) -> BusinessDocumentType:
        return BusinessDocumentType.REGISTRATION_CERTIFICATE

    def supports(self, document: StructuredDocument) -> bool:
        if document.document_family != DocumentFamily.IDENTITY_DOCUMENT and document.document_family != DocumentFamily.CERTIFICATE:
            return False
            
        text = document.extracted_text.upper()
        if "REGISTRATION" in text and "VEHICLE" in text:
            return True
            
        return False

    def validate(self, document: StructuredDocument) -> List[ValidationIssue]:
        # generic identity doc might output entity_id
        return validate_required_fields(
            document, 
            ["entity_id"]
        )

    def interpret(self, document: StructuredDocument) -> List[Any]:
        field_map = {f.name: f.value for f in document.structured_fields}
        
        reg_no = str(field_map.get("entity_id", "UNKNOWN"))
        
        event = VehicleRegistrationUpdated(
            source_document_id=str(document.document_id),
            registration_number=reg_no
        )
        return [event]
