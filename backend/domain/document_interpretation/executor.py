"""
FleetGuard Document Interpretation - Executor
"""

import time
import logging
import traceback
from infrastructure.documents.models import StructuredDocument
from domain.document_interpretation.registry import DocumentInterpreterRegistry
from domain.document_interpretation.models import InterpretationResult, BusinessDocumentType, ValidationIssue


logger = logging.getLogger(__name__)


class DocumentInterpretationExecutor:
    """
    Executes the FleetGuard business interpretation pipeline for generic StructuredDocuments.
    """
    def __init__(self, registry: DocumentInterpreterRegistry):
        self.registry = registry

    def process_document(self, document: StructuredDocument) -> InterpretationResult:
        start_time = time.perf_counter()
        
        try:
            # 1. Discover Interpreter via Strategy Pattern
            interpreter = self.registry.find_interpreter(document)
            
            if not interpreter:
                # If truly nothing supports it (not even Unknown), default to UNKNOWN
                return InterpretationResult(
                    structured_document_id=str(document.document_id),
                    business_document_type=BusinessDocumentType.UNKNOWN,
                    validation_results=[ValidationIssue(
                        field_name="document",
                        severity="ERROR",
                        error_code="NO_INTERPRETER_FOUND",
                        message="No business interpreter supports this document."
                    )],
                    metadata={"execution_time_ms": (time.perf_counter() - start_time) * 1000}
                )

            business_type = interpreter.get_business_type()
            
            # 2. Execute Business Validation
            try:
                validation_results = interpreter.validate(document)
            except Exception as e:
                logger.error(f"Business validation failed: {str(e)}")
                return InterpretationResult(
                    structured_document_id=str(document.document_id),
                    business_document_type=business_type,
                    validation_results=[ValidationIssue(
                        field_name="document",
                        severity="ERROR",
                        error_code="VALIDATION_EXCEPTION",
                        message=f"Validation crashed: {str(e)}"
                    )],
                    metadata={"execution_time_ms": (time.perf_counter() - start_time) * 1000}
                )

            # 3. Generate Operational Events (only if validation passes cleanly)
            operational_events = []
            has_errors = any(issue.severity == "ERROR" for issue in validation_results)
            
            if not has_errors:
                try:
                    operational_events = interpreter.interpret(document)
                except Exception as e:
                    logger.error(f"Interpretation failed: {str(e)}")
                    validation_results.append(ValidationIssue(
                        field_name="document",
                        severity="ERROR",
                        error_code="INTERPRETATION_EXCEPTION",
                        message=f"Event generation crashed: {str(e)}"
                    ))

            # 4. Return InterpretationResult
            return InterpretationResult(
                structured_document_id=str(document.document_id),
                business_document_type=business_type,
                operational_events=operational_events,
                validation_results=validation_results,
                metadata={"execution_time_ms": (time.perf_counter() - start_time) * 1000}
            )

        except Exception as e:
            logger.error(f"Document interpretation pipeline failed: {str(e)}")
            logger.debug(traceback.format_exc())
            return InterpretationResult(
                structured_document_id=str(document.document_id),
                business_document_type=BusinessDocumentType.UNKNOWN,
                validation_results=[ValidationIssue(
                    field_name="system",
                    severity="ERROR",
                    error_code="SYSTEM_EXCEPTION",
                    message=f"System error: {str(e)}"
                )],
                metadata={"execution_time_ms": (time.perf_counter() - start_time) * 1000}
            )
