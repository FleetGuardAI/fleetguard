"""
Document Intelligence Framework - Generic Invoice Parser
"""
import uuid
from typing import List
from infrastructure.documents.base import BaseDocumentParser
from infrastructure.documents.models import DocumentFamily, ExtractedField

class InvoiceParser(BaseDocumentParser):
    @classmethod
    def key(cls) -> str:
        return "invoice_parser"

    @classmethod
    def supports(cls) -> DocumentFamily:
        return DocumentFamily.INVOICE

    def parse(self, extracted_text: str) -> List[ExtractedField]:
        # Mock structured extraction
        return [
            ExtractedField(name="invoice_number", value=str(uuid.uuid4())[:8], confidence=0.9, source_info="regex_match"),
            ExtractedField(name="total_amount", value="150.00", confidence=0.85, source_info="regex_match"),
            ExtractedField(name="date", value="2026-07-20", confidence=0.95, source_info="date_parser")
        ]
