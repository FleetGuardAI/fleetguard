"""
FleetGuard Document Interpretation - Unknown Document
"""

from typing import List, Any
from domain.document_interpretation.base import BaseDocumentInterpreter
from domain.document_interpretation.models import BusinessDocumentType, ValidationIssue
from infrastructure.documents.models import StructuredDocument


class UnknownInterpreter(BaseDocumentInterpreter):
    @classmethod
    def key(cls) -> str:
        return "unknown_interpreter"

    @classmethod
    def get_business_type(cls) -> BusinessDocumentType:
        return BusinessDocumentType.UNKNOWN

    def supports(self, document: StructuredDocument) -> bool:
        # Fallback interpreter. Always supports if we reach this point.
        # But in a strategy pattern, we should just let it be the last registered.
        return True

    def validate(self, document: StructuredDocument) -> List[ValidationIssue]:
        return []

    def interpret(self, document: StructuredDocument) -> List[Any]:
        return []
