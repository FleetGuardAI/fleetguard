"""
FleetGuard Document Interpretation - Fuel Receipt
"""

from typing import List, Any
from domain.document_interpretation.base import BaseDocumentInterpreter
from domain.document_interpretation.models import BusinessDocumentType, ValidationIssue
from domain.document_interpretation.validators import validate_required_fields
from domain.document_interpretation.events import FuelPurchaseRecorded
from infrastructure.documents.models import StructuredDocument, DocumentFamily


class FuelReceiptInterpreter(BaseDocumentInterpreter):
    @classmethod
    def key(cls) -> str:
        return "fuel_receipt_interpreter"

    @classmethod
    def get_business_type(cls) -> BusinessDocumentType:
        return BusinessDocumentType.FUEL_RECEIPT

    def supports(self, document: StructuredDocument) -> bool:
        """
        Supports RECEIPT family if it contains fuel-specific keywords in text or fields.
        """
        if document.document_family != DocumentFamily.RECEIPT:
            return False
            
        text = document.extracted_text.upper()
        if "FUEL" in text or "PETROL" in text or "DIESEL" in text:
            return True
            
        return False

    def validate(self, document: StructuredDocument) -> List[ValidationIssue]:
        return validate_required_fields(
            document, 
            ["total_paid", "date"] # Suppose we expect these from generic receipt parser
        )

    def interpret(self, document: StructuredDocument) -> List[Any]:
        # Extract generic fields
        field_map = {f.name: f.value for f in document.structured_fields}
        
        # In a real scenario, we'd map this safely. For now, simulate:
        total_paid = float(field_map.get("total_paid", 0.0))
        date = str(field_map.get("date", "2026-07-20"))
        fuel_qty = 0.0 # Suppose generic receipt doesn't get this easily, we default
        
        event = FuelPurchaseRecorded(
            source_document_id=str(document.document_id),
            fuel_quantity=fuel_qty,
            total_amount=total_paid,
            purchase_date=date
        )
        return [event]
