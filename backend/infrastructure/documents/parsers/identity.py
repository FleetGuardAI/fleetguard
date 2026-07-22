"""
Document Intelligence Framework - Generic Identity Parser
"""
from typing import List
from infrastructure.documents.base import BaseDocumentParser
from infrastructure.documents.models import DocumentFamily, ExtractedField

class IdentityDocumentParser(BaseDocumentParser):
    @classmethod
    def key(cls) -> str:
        return "identity_parser"

    @classmethod
    def supports(cls) -> DocumentFamily:
        return DocumentFamily.IDENTITY_DOCUMENT

    def parse(self, extracted_text: str) -> List[ExtractedField]:
        return [
            ExtractedField(name="entity_id", value="ID-9999", confidence=0.99, source_info="regex_match"),
            ExtractedField(name="entity_name", value="John Doe", confidence=0.8, source_info="ner")
        ]
