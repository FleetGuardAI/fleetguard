"""
Document Intelligence Framework - Classifiers
"""

from infrastructure.documents.models import DocumentFamily


def classify_document(extracted_text: str) -> DocumentFamily:
    """
    Deterministically classifies a document into a generic DocumentFamily 
    based on the extracted text contents.
    
    This is a generic classifier. It identifies structural document shapes
    (like "INVOICE") rather than business-specific types (like "Tyre Invoice").
    Business specific interpretation happens downstream.
    """
    text_upper = extracted_text.upper()
    
    if "INVOICE" in text_upper or "BILL" in text_upper:
        return DocumentFamily.INVOICE
        
    if "RECEIPT" in text_upper:
        return DocumentFamily.RECEIPT
        
    if "CERTIFICATE" in text_upper or "PUC" in text_upper or "POLLUTION" in text_upper:
        return DocumentFamily.CERTIFICATE
        
    if "LICENSE" in text_upper or "LICENCE" in text_upper or "REGISTRATION" in text_upper or "IDENTITY" in text_upper:
        return DocumentFamily.IDENTITY_DOCUMENT
        
    if "FORM" in text_upper or "APPLICATION" in text_upper:
        return DocumentFamily.FORM
        
    return DocumentFamily.UNKNOWN
