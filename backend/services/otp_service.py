"""
FleetGuard — OTP Service (MSG91 Widget Provider implementation)
"""

import logging
import httpx
import uuid
from typing import Optional

from config import settings
from services.otp_provider import OTPProvider, OTPRequestResult, OTPVerificationResult

logger = logging.getLogger("fleetguard.otp")

class MSG91OTPProvider(OTPProvider):
    """
    Official MSG91 OTP Widget API integration.
    Handles OTP generation, delivery, retry, and verification externally.
    """
    def __init__(self):
        self.auth_key = settings.MSG91_AUTH_KEY
        self.widget_id = settings.MSG91_WIDGET_ID
        self.widget_token = settings.MSG91_WIDGET_TOKEN
        
        if not self.auth_key or not self.widget_id or not self.widget_token:
            logger.warning("MSG91 credentials are not fully configured!")
            
    def _get_headers(self):
        return {
            "authkey": self.auth_key or "",
            "widgetToken": self.widget_token or "",
            "Content-Type": "application/json"
        }

    async def request_otp(self, identifier: str) -> OTPRequestResult:
        if not self.auth_key:
            return OTPRequestResult(False, "MSG91 not fully configured")
            
        url = "https://api.msg91.com/api/v5/widget/sendOtp"
        payload = {
            "widgetId": self.widget_id,
            "identifier": identifier
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self._get_headers())
                data = response.json()
                
                if data.get("type") == "success":
                    req_id = data.get("message") # Often reqId is returned in message or response
                    # If it's a dict, check for reqId
                    if isinstance(data.get("message"), str) and len(data.get("message")) > 10:
                        req_id = data.get("message")
                    else:
                        req_id = data.get("reqId") or data.get("request_id")
                        
                    logger.info(f"MSG91 OTP requested for {identifier}")
                    return OTPRequestResult(True, "OTP sent successfully", provider_reference=req_id)
                else:
                    logger.error(f"MSG91 request failed: {data}")
                    return OTPRequestResult(False, "Failed to send OTP via provider")
        except Exception as e:
            logger.error(f"MSG91 API exception: {e}")
            return OTPRequestResult(False, "Provider API error")

    async def retry_otp(self, req_id: str, channel: str = "SMS") -> OTPRequestResult:
        if not self.auth_key:
            return OTPRequestResult(False, "MSG91 not fully configured")
            
        url = "https://api.msg91.com/api/v5/widget/retryOtp"
        payload = {
            "widgetId": self.widget_id,
            "reqId": req_id,
            "retryType": channel # e.g., 'text' or 'voice'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self._get_headers())
                data = response.json()
                
                if data.get("type") == "success":
                    logger.info(f"MSG91 OTP retried for reqId {req_id}")
                    return OTPRequestResult(True, "OTP resent successfully", provider_reference=req_id)
                else:
                    logger.error(f"MSG91 retry failed: {data}")
                    return OTPRequestResult(False, "Failed to resend OTP via provider")
        except Exception as e:
            logger.error(f"MSG91 API exception: {e}")
            return OTPRequestResult(False, "Provider API error")

    async def verify_otp(self, req_id: str, code: str) -> OTPVerificationResult:
        if not self.auth_key:
            return OTPVerificationResult(False, "MSG91 not fully configured")
            
        url = "https://api.msg91.com/api/v5/widget/verifyOtp"
        payload = {
            "widgetId": self.widget_id,
            "reqId": req_id,
            "otp": code
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self._get_headers())
                data = response.json()
                
                if data.get("type") == "success":
                    logger.info(f"MSG91 OTP verified for reqId {req_id}")
                    return OTPVerificationResult(True, "OTP verified successfully")
                else:
                    logger.warning(f"MSG91 verification failed for reqId {req_id}: {data}")
                    return OTPVerificationResult(False, "Invalid or expired OTP")
        except Exception as e:
            logger.error(f"MSG91 API exception: {e}")
            return OTPVerificationResult(False, "Provider API error")


class MockOTPProvider(OTPProvider):
    """
    Mock provider for local development and automated testing.
    Requires OTP_MOCK_MODE=True in configuration.
    """
    def __init__(self):
        if not settings.OTP_MOCK_MODE:
            logger.error("MockOTPProvider instantiated but OTP_MOCK_MODE is false!")

    async def request_otp(self, identifier: str) -> OTPRequestResult:
        if not settings.OTP_MOCK_MODE:
            return OTPRequestResult(False, "Mock mode disabled")
        logger.info(f"[MOCK] OTP requested for {identifier}")
        # Generate a fake req_id
        mock_req_id = f"mock_req_{uuid.uuid4().hex[:12]}"
        return OTPRequestResult(True, "Mock OTP sent (use 123456)", provider_reference=mock_req_id)

    async def retry_otp(self, req_id: str, channel: str = "SMS") -> OTPRequestResult:
        if not settings.OTP_MOCK_MODE:
            return OTPRequestResult(False, "Mock mode disabled")
        logger.info(f"[MOCK] OTP retried for {req_id}")
        return OTPRequestResult(True, "Mock OTP resent (use 123456)", provider_reference=req_id)

    async def verify_otp(self, req_id: str, code: str) -> OTPVerificationResult:
        if not settings.OTP_MOCK_MODE:
            return OTPVerificationResult(False, "Mock mode disabled")
            
        if code == "123456" and req_id.startswith("mock_req_"):
            logger.info(f"[MOCK] OTP verified for reqId {req_id}")
            return OTPVerificationResult(True, "Mock OTP verified")
            
        logger.warning(f"[MOCK] OTP verification failed for reqId {req_id}")
        return OTPVerificationResult(False, "Invalid mock OTP or reqId")


def get_otp_provider() -> OTPProvider:
    """Factory to return the configured OTP Provider."""
    if settings.OTP_MOCK_MODE:
        return MockOTPProvider()
        
    provider_name = getattr(settings, 'OTP_PROVIDER', 'MSG91').upper()
    if provider_name == 'MSG91':
        return MSG91OTPProvider()
        
    logger.error(f"Unknown OTP_PROVIDER {provider_name}, falling back to Mock (WARNING)")
    return MockOTPProvider()

# Singleton usage
otp_provider = get_otp_provider()
