"""
Attachment Processing Framework - Routing
"""

from infrastructure.attachments.models import Attachment


def determine_processor_route(attachment: Attachment) -> str:
    """
    Deterministically routes an attachment to a specific downstream processor
    based purely on its MIME metadata. Does NOT interpret the contents.
    
    Returns the routing destination string (e.g. queue/topic name).
    Raises ValueError if routing cannot be resolved.
    """
    mime = attachment.mime_type.lower()
    
    if mime.startswith("image/"):
        return "ImageProcessor"
    
    if mime == "application/pdf":
        return "DocumentProcessor"
        
    if mime.startswith("audio/"):
        return "AudioProcessor"
        
    if mime.startswith("video/"):
        return "VideoProcessor"

    raise ValueError(f"Cannot resolve routing for MIME type '{mime}'.")
