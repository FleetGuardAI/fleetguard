"""
FleetGuard — Processing Result Schema
"""

import enum
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field


class ProcessingStatus(str, enum.Enum):
    """
    The overall outcome of the Processing Engine execution.
    """
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessingResult(BaseModel):
    """
    The structured result of the Processing Engine's execution.
    Serialized and attached to the PROCESSING_COMPLETED/FAILED event payload.
    """
    processed_domains: List[str] = Field(default_factory=list, description="All domains that were intended to be invoked.")
    successful_domains: List[str] = Field(default_factory=list, description="Domains that completed successfully.")
    failed_domains: List[Dict[str, Any]] = Field(default_factory=list, description="Domains that failed (domain, error).")
    skipped_domains: List[str] = Field(default_factory=list, description="Domains that were skipped due to previous failures or conditions.")
    
    processing_status: ProcessingStatus = Field(..., description="The overall processing outcome.")
    processing_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds.")
    
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Top-level errors (if any).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata.")
