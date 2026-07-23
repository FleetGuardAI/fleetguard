"""
Document Intelligence Framework - Generic Form Parser
"""
from typing import List
from infrastructure.documents.base import BaseDocumentParser
from infrastructure.documents.models import DocumentFamily, ExtractedField

class FormParser(BaseDocumentParser):
    @classmethod
    def key(cls) -> str:
        return "form_parser"

    @classmethod
    def supports(cls) -> DocumentFamily:
        return DocumentFamily.FORM

    def parse(self, extracted_text: str) -> List[ExtractedField]:
        return [
            ExtractedField(name="form_type", value="Standard Application", confidence=0.7, source_info="keyword_match"),
            ExtractedField(name="signature_present", value=True, confidence=0.9, source_info="layout_analysis")
        ]
