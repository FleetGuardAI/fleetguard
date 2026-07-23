"""
FleetGuard Document Interpretation Framework - Validators
"""

from typing import List
from infrastructure.documents.models import StructuredDocument
from domain.document_interpretation.models import ValidationIssue


def validate_required_fields(document: StructuredDocument, required_fields: List[str]) -> List[ValidationIssue]:
    """
    Validates that a StructuredDocument contains the specified required fields.
    Returns a list of ValidationIssues for missing fields.
    """
    issues = []
    
    extracted_names = {f.name for f in document.structured_fields}
    
    for field in required_fields:
        if field not in extracted_names:
            issues.append(
                ValidationIssue(
                    field_name=field,
                    severity="ERROR",
                    error_code="MISSING_REQUIRED_FIELD",
                    message=f"Required business field '{field}' was not found in the document."
                )
            )
            
    # Also check if any existing required field has a null value
    for f in document.structured_fields:
        if f.name in required_fields and (f.value is None or str(f.value).strip() == ""):
            issues.append(
                ValidationIssue(
                    field_name=f.name,
                    severity="ERROR",
                    error_code="EMPTY_REQUIRED_FIELD",
                    message=f"Required business field '{f.name}' was found but contains an empty value."
                )
            )

    return issues
