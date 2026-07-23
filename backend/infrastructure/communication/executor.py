"""
Message Gateway Framework - Executor
"""

import time
import logging
import traceback
from typing import Dict, Any

from infrastructure.communication.models import CommunicationProcessingResult, CommunicationProcessingStatus
from infrastructure.communication.registry import CommunicationChannelRegistry


logger = logging.getLogger(__name__)


class CommunicationGatewayExecutor:
    """
    Executes the reception of a webhook payload through a specific channel.
    Resolves the channel, triggers the validation and normalization lifecycle,
    and returns an immutable CommunicationProcessingResult.
    """
    def __init__(self, registry: CommunicationChannelRegistry):
        self.registry = registry

    def process_webhook(self, channel_key: str, payload: Dict[str, Any]) -> CommunicationProcessingResult:
        """
        Processes an incoming webhook for the specified channel key.
        Catches and isolates failures, mapping them to the appropriate CommunicationProcessingStatus.
        """
        start_time = time.perf_counter()
        
        try:
            channel_class = self.registry.get_channel(channel_key)
            channel = channel_class()
            
            message = channel.receive(payload)
            
            execution_time = time.perf_counter() - start_time
            return CommunicationProcessingResult(
                message=message,
                processing_status=CommunicationProcessingStatus.SUCCESS,
                execution_time=execution_time
            )
            
        except KeyError as e:
            execution_time = time.perf_counter() - start_time
            return CommunicationProcessingResult(
                processing_status=CommunicationProcessingStatus.SYSTEM_ERROR,
                error_message=f"Channel resolution failed: {str(e)}",
                execution_time=execution_time
            )
        except ValueError as e:
            # Often used for validation/normalization logic errors
            execution_time = time.perf_counter() - start_time
            return CommunicationProcessingResult(
                processing_status=CommunicationProcessingStatus.VALIDATION_ERROR,
                error_message=str(e),
                execution_time=execution_time
            )
        except Exception as e:
            logger.error(f"Communication Gateway failed processing webhook for channel '{channel_key}': {str(e)}")
            logger.debug(traceback.format_exc())
            execution_time = time.perf_counter() - start_time
            return CommunicationProcessingResult(
                processing_status=CommunicationProcessingStatus.SYSTEM_ERROR,
                error_message=f"System error: {str(e)}",
                execution_time=execution_time
            )
