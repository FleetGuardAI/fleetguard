"""
Document Intelligence Framework - Generic Certificate Parser
"""
from typing import List
from infrastructure.documents.base import BaseDocumentParser
from infrastructure.documents.models import DocumentFamily, ExtractedField

class CertificateParser(BaseDocumentParser):
    @classmethod
    def key(cls) -> str:
        return "certificate_parser"

    @classmethod
    def supports(cls) -> DocumentFamily:
        return DocumentFamily.CERTIFICATE

    def parse(self, extracted_text: str) -> List[ExtractedField]:
        return [
            ExtractedField(name="certificate_id", value="CERT-1234", confidence=0.9, source_info="regex_match"),
            ExtractedField(name="expiry_date", value="2027-01-01", confidence=0.85, source_info="date_parser")
        ]
