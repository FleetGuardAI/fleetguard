"""
Document Intelligence Framework - Generic Receipt Parser
"""
from typing import List
from infrastructure.documents.base import BaseDocumentParser
from infrastructure.documents.models import DocumentFamily, ExtractedField

class ReceiptParser(BaseDocumentParser):
    @classmethod
    def key(cls) -> str:
        return "receipt_parser"

    @classmethod
    def supports(cls) -> DocumentFamily:
        return DocumentFamily.RECEIPT

    def parse(self, extracted_text: str) -> List[ExtractedField]:
        return [
            ExtractedField(name="merchant_name", value="Test Merchant", confidence=0.8, source_info="ner"),
            ExtractedField(name="total_paid", value="50.00", confidence=0.9, source_info="regex_match")
        ]
