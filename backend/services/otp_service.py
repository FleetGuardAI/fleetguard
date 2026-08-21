"""
FleetGuard — OTP Service (MSG91 Widget Provider implementation)
"""

import logging
import httpx
import uuid
import json
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
            "tokenAuth": self.widget_token or "",
            "Content-Type": "application/json"
        }

    async def request_otp(self, identifier: str) -> OTPRequestResult:
        if not self.auth_key:
            return OTPRequestResult(False, "MSG91 not fully configured")
            
        # Normalize identifier exactly like the frontend does (remove + and ensure 91 prefix)
        cleaned_id = "".join(filter(str.isdigit, identifier))
        if len(cleaned_id) == 10:
            cleaned_id = f"91{cleaned_id}"
            
        url = "https://api.msg91.com/api/v5/widget/sendOtp"
        payload = {
            "widgetId": self.widget_id,
            "identifier": cleaned_id
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
                    error_detail = data.get("message", "Unknown MSG91 error")
                    diagnostic = f"widgetId_present: {bool(self.widget_id)}, auth_present: {bool(self.auth_key)}"
                    return OTPRequestResult(False, f"MSG91 Error: {error_detail} | {diagnostic}")
        except Exception as e:
            logger.error(f"MSG91 API exception: {e}")
            return OTPRequestResult(False, f"Provider API error: {str(e)}")

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

    async def verify_access_token(self, token: str) -> OTPVerificationResult:
        if not self.auth_key:
            return OTPVerificationResult(False, "MSG91 not fully configured")
            
        url = "https://api.msg91.com/api/v5/widget/verifyAccessToken"
        payload = {
            "access-token": token
        }
        
        logger.info(f"[MSG91 DEBUG] verifyAccessToken diagnostic: " + json.dumps({
            "tokenPresent": bool(token),
            "tokenLength": len(token) if token else 0,
            "widgetIdConfigured": bool(getattr(settings, 'MSG91_WIDGET_ID', None)),
            "authKeyConfigured": bool(self.auth_key)
        }))
        
        logger.info("[MSG91 DEBUG] access-token verification started")
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "authkey": self.auth_key or "",
                    "Content-Type": "application/json"
                }
                response = await client.post(url, json=payload, headers=headers)
                logger.info(f"[MSG91 DEBUG] MSG91 response status: {response.status_code}")
                
                try:
                    data = response.json()
                    logger.info(f"[MSG91 DEBUG] MSG91 response keys: {list(data.keys())}")
                    
                    if data.get("type") == "error":
                         logger.warning(f"[MSG91 DEBUG] MSG91 returned error type: {data.get('message')}")
                except Exception:
                    data = {}
                    logger.warning(f"[MSG91 DEBUG] MSG91 response was not valid JSON")
                
                # Check for success format: either {"type": "success"} or similar.
                # If msg91 fails, it usually returns error type or code
                if data.get("type") == "success" or data.get("message") == "Token verified":
                    logger.info("[MSG91 DEBUG] MSG91 access-token verification successful: True")
                    return OTPVerificationResult(True, "Access Token verified successfully")
                else:
                    logger.info("[MSG91 DEBUG] MSG91 access-token verification successful: False")
                    logger.warning(f"MSG91 access token verification failed: {data}")
                    return OTPVerificationResult(False, "Invalid access token")
        except Exception as e:
            logger.error(f"MSG91 API exception during token verify: {e}")
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

    async def verify_access_token(self, token: str) -> OTPVerificationResult:
        if not settings.OTP_MOCK_MODE:
            return OTPVerificationResult(False, "Mock mode disabled")
            
        if token.startswith("mock_token_"):
            logger.info("[MOCK] Access Token verified")
            return OTPVerificationResult(True, "Mock Access Token verified")
            
        logger.warning("[MOCK] Access Token verification failed")
        return OTPVerificationResult(False, "Invalid mock token")


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
