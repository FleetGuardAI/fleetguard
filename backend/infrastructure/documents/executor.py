"""
Document Intelligence Framework - Executor
"""

import time
import logging
import traceback
from infrastructure.attachments.models import Attachment
from infrastructure.documents.registry import DocumentParserRegistry
from infrastructure.documents.extractors import select_extraction_strategy
from infrastructure.documents.classifiers import classify_document
from infrastructure.documents.models import StructuredDocument, DocumentProcessingResult, DocumentProcessingStatus


logger = logging.getLogger(__name__)


class DocumentProcessingExecutor:
    """
    Executes the deterministic document understanding pipeline.
    Pipelines an attachment through Extraction -> Classification -> Parsing.
    """
    def __init__(self, registry: DocumentParserRegistry):
        self.registry = registry

    def process_attachment(self, attachment: Attachment) -> DocumentProcessingResult:
        start_time = time.perf_counter()
        
        try:
            # 1. Determine Extraction Strategy
            extractor = select_extraction_strategy(attachment)
            
            # 2. Extract Text
            try:
                extracted_text, diagnostics = extractor.extract(attachment)
            except Exception as e:
                return DocumentProcessingResult(
                    processing_status=DocumentProcessingStatus.EXTRACTION_FAILED,
                    error_message=f"Extraction failed: {str(e)}",
                    execution_time=time.perf_counter() - start_time
                )
                
            # 3. Classify Document Type
            try:
                document_family = classify_document(extracted_text)
            except Exception as e:
                return DocumentProcessingResult(
                    processing_status=DocumentProcessingStatus.CLASSIFICATION_FAILED,
                    error_message=f"Classification failed: {str(e)}",
                    execution_time=time.perf_counter() - start_time
                )
                
            # 4. Select Parser
            try:
                parser_class = self.registry.get_parser_by_family(document_family)
                parser = parser_class()
            except KeyError:
                # If we classified it but have no parser registered for that family
                return DocumentProcessingResult(
                    processing_status=DocumentProcessingStatus.UNKNOWN_TYPE,
                    error_message=f"No parser available for document family {document_family.value}",
                    execution_time=time.perf_counter() - start_time
                )
                
            # 5. Parse Structured Fields
            try:
                structured_fields = parser.parse(extracted_text)
            except Exception as e:
                return DocumentProcessingResult(
                    processing_status=DocumentProcessingStatus.PARSING_FAILED,
                    error_message=f"Parsing failed: {str(e)}",
                    execution_time=time.perf_counter() - start_time
                )
                
            # 6. Produce StructuredDocument
            structured_document = StructuredDocument(
                attachment_id=str(attachment.attachment_id),
                document_family=document_family,
                extraction_method=extractor.name(),
                extracted_text=extracted_text,
                structured_fields=structured_fields,
                diagnostics=diagnostics
            )
            
            return DocumentProcessingResult(
                structured_document=structured_document,
                processing_status=DocumentProcessingStatus.SUCCESS,
                execution_time=time.perf_counter() - start_time
            )
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            logger.debug(traceback.format_exc())
            return DocumentProcessingResult(
                processing_status=DocumentProcessingStatus.PARSING_FAILED,
                error_message=f"System error: {str(e)}",
                execution_time=time.perf_counter() - start_time
            )
