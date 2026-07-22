"""
Document Intelligence Framework - Base Parser
"""

import abc
from typing import List
from infrastructure.documents.models import DocumentFamily, ExtractedField


class BaseDocumentParser(abc.ABC):
    """
    Abstract Base Class for structural document parsers.
    Parsers are responsible for extracting structured fields from raw text
    based on the document family.
    """

    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """
        Returns the unique identifier of this parser (e.g., 'invoice_parser').
        """
        pass

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    @abc.abstractmethod
    def supports(cls) -> DocumentFamily:
        """
        Returns the generic DocumentFamily this parser is designed for.
        """
        pass

    @abc.abstractmethod
    def parse(self, extracted_text: str) -> List[ExtractedField]:
        """
        Parses the raw extracted text into structured, immutable fields.
        Does NOT apply business logic or decision making.
        """
        pass
