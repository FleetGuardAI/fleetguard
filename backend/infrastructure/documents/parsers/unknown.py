"""
Document Intelligence Framework - Generic Unknown Parser
"""
from typing import List
from infrastructure.documents.base import BaseDocumentParser
from infrastructure.documents.models import DocumentFamily, ExtractedField

class UnknownParser(BaseDocumentParser):
    @classmethod
    def key(cls) -> str:
        return "unknown_parser"

    @classmethod
    def supports(cls) -> DocumentFamily:
        return DocumentFamily.UNKNOWN

    def parse(self, extracted_text: str) -> List[ExtractedField]:
        return [
            ExtractedField(name="raw_text_length", value=len(extracted_text), confidence=1.0, source_info="system")
        ]
