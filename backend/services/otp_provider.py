"""
FleetGuard — OTP Provider Interface
Abstracts OTP generation and delivery from FleetGuard logic.
"""

from abc import ABC, abstractmethod
from typing import Optional

class OTPRequestResult:
    def __init__(self, success: bool, message: str, provider_reference: Optional[str] = None):
        self.success = success
        self.message = message
        self.provider_reference = provider_reference

class OTPVerificationResult:
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message

class OTPProvider(ABC):
    """
    Abstract interface for OTP generation and verification.
    """
    
    @abstractmethod
    async def request_otp(self, identifier: str) -> OTPRequestResult:
        """
        Request the provider to generate and send an OTP.
        """
        pass
        
    @abstractmethod
    async def verify_otp(self, req_id: str, code: str) -> OTPVerificationResult:
        """
        Request the provider to verify an entered OTP using the req_id.
        """
        pass

    @abstractmethod
    async def retry_otp(self, req_id: str, channel: str = "SMS") -> OTPRequestResult:
        """
        Retry sending the OTP for a specific request ID.
        """
        pass
