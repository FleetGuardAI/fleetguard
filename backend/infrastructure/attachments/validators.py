"""
Attachment Processing Framework - Validators
"""

from typing import List
from infrastructure.attachments.models import Attachment

def validate_max_size(attachment: Attachment, max_bytes: int = 50 * 1024 * 1024) -> bool:
    """
    Validates that the file does not exceed the maximum allowed size.
    Default max is 50MB.
    """
    if attachment.file_size is not None and attachment.file_size > max_bytes:
        raise ValueError(f"File size {attachment.file_size} exceeds maximum {max_bytes} bytes.")
    return True


def validate_mime_type(attachment: Attachment, allowed_prefixes: List[str] = None) -> bool:
    """
    Validates the attachment's mime_type against a list of allowed prefixes 
    (e.g., ['image/', 'application/pdf', 'audio/', 'video/']).
    """
    if not allowed_prefixes:
        allowed_prefixes = ["image/", "application/pdf", "audio/", "video/"]
        
    mime = attachment.mime_type.lower()
    if not any(mime.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError(f"MIME type '{attachment.mime_type}' is not supported.")
    return True


def validate_missing_file_reference(attachment: Attachment) -> bool:
    """
    Validates that the storage_uri is present (meaning a file was actually provided).
    """
    if not attachment.storage_uri:
        raise ValueError("Attachment is missing a storage_uri.")
    return True
