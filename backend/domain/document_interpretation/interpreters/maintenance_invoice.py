"""
FleetGuard Document Interpretation - Maintenance Invoice
"""

from typing import List, Any
from domain.document_interpretation.base import BaseDocumentInterpreter
from domain.document_interpretation.models import BusinessDocumentType, ValidationIssue
from domain.document_interpretation.validators import validate_required_fields
from domain.document_interpretation.events import MaintenancePerformed
from infrastructure.documents.models import StructuredDocument, DocumentFamily


class MaintenanceInvoiceInterpreter(BaseDocumentInterpreter):
    @classmethod
    def key(cls) -> str:
        return "maintenance_invoice_interpreter"

    @classmethod
    def get_business_type(cls) -> BusinessDocumentType:
        return BusinessDocumentType.MAINTENANCE_INVOICE

    def supports(self, document: StructuredDocument) -> bool:
        if document.document_family != DocumentFamily.INVOICE:
            return False
            
        text = document.extracted_text.upper()
        if "MAINTENANCE" in text or "SERVICE" in text or "REPAIR" in text:
            return True
            
        return False

    def validate(self, document: StructuredDocument) -> List[ValidationIssue]:
        return validate_required_fields(
            document, 
            ["total_amount", "date"]
        )

    def interpret(self, document: StructuredDocument) -> List[Any]:
        field_map = {f.name: f.value for f in document.structured_fields}
        
        total = float(field_map.get("total_amount", 0.0))
        date = str(field_map.get("date", "2026-07-20"))
        
        event = MaintenancePerformed(
            source_document_id=str(document.document_id),
            total_amount=total,
            service_date=date
        )
        return [event]
