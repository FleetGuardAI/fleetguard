"""
Attachment Processing Framework - Executor
"""

import time
import logging
import traceback

from infrastructure.attachments.models import Attachment, AttachmentProcessingResult, AttachmentStatus
from infrastructure.attachments.registry import AttachmentHandlerRegistry
from infrastructure.attachments.repository import AttachmentRepository
from infrastructure.attachments.routing import determine_processor_route
from infrastructure.attachments.validators import validate_missing_file_reference


logger = logging.getLogger(__name__)


class AttachmentProcessingExecutor:
    """
    Executes the reception and processing lifecycle for an inbound Attachment.
    Orchestrates validation, duplicate detection, metadata persistence, and routing.
    """
    def __init__(self, registry: AttachmentHandlerRegistry, repository: AttachmentRepository):
        self.registry = registry
        self.repository = repository

    def process_attachment(self, handler_key: str, attachment: Attachment) -> AttachmentProcessingResult:
        """
        Processes an attachment against the designated handler.
        """
        start_time = time.perf_counter()
        
        try:
            # 1. Resolve Handler
            handler_class = self.registry.get_handler(handler_key)
            handler = handler_class()
            
            # 2. General Validation
            validate_missing_file_reference(attachment)
            
            # 3. Handler-Specific Validation
            handler.validate(attachment)
            
            # 4. Duplicate Detection (via Checksum)
            if attachment.checksum and self.repository.exists_by_checksum(attachment.checksum):
                return AttachmentProcessingResult(
                    attachment=attachment,
                    processing_status=AttachmentStatus.DUPLICATE,
                    execution_time=time.perf_counter() - start_time
                )
            
            # 5. Determine Media Type & Route
            # Ensures the attachment matches the handler's capabilities
            media_type = handler.determine_media_type(attachment)
            routed_processor = handler.route(attachment)
            
            # 6. Persist Metadata
            self.repository.save(attachment)
            
            return AttachmentProcessingResult(
                attachment=attachment,
                processing_status=AttachmentStatus.ROUTED,
                routed_processor=routed_processor,
                execution_time=time.perf_counter() - start_time
            )
            
        except KeyError as e:
            return AttachmentProcessingResult(
                attachment=attachment,
                processing_status=AttachmentStatus.FAILED,
                error_message=f"Handler resolution failed: {str(e)}",
                execution_time=time.perf_counter() - start_time
            )
        except ValueError as e:
            return AttachmentProcessingResult(
                attachment=attachment,
                processing_status=AttachmentStatus.FAILED,
                error_message=str(e),
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            logger.error(f"Attachment Processing failed: {str(e)}")
            logger.debug(traceback.format_exc())
            return AttachmentProcessingResult(
                attachment=attachment,
                processing_status=AttachmentStatus.FAILED,
                error_message=f"System error: {str(e)}",
                execution_time=time.perf_counter() - start_time
            )
