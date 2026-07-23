"""
FleetGuard — Dead Letter Queue Schema
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FailureCategory(str, Enum):
    """Broad categorization of failures for operational dashboards."""
    DESERIALIZATION = "DESERIALIZATION"
    VALIDATION = "VALIDATION"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


class DeadLetterMessage(BaseModel):
    """
    Schema representing a poisoned or chronically failing message routed to the DLQ.
    Serves as a complete forensic record for debugging and eventual replay.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Kafka Origin
    original_topic: str
    original_partition: int
    original_offset: int
    
    # Traceability
    event_id: Optional[str] = None
    correlation_id: Optional[str] = None  # Future milestone
    causation_id: Optional[str] = None    # Future milestone
    
    # Forensic Data
    payload: str = Field(description="The exact payload exactly as it was received, un-truncated.")
    
    # Failure Details
    failure_category: FailureCategory
    exception_type: str
    exception_message: str
    stack_trace: Optional[str] = None
    retry_attempts: int
    failed_at: datetime
    consumer_name: str
