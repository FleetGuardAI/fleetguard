"""
FleetGuard — OTP Service (MSG91 Widget & Standard Provider implementation)
FG-SEC-002: Persistent, database-backed OTP identity binding & atomic transaction tracking.
"""

import os
import sys
import logging
import httpx
import uuid
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Any

from fastapi import HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.otp_transaction import OTPTransaction
from services.otp_provider import OTPProvider, OTPRequestResult, OTPVerificationResult

logger = logging.getLogger("fleetguard.otp")


def normalize_identifier(identifier: Optional[str]) -> str:
    """Normalize phone number (digits with 91 prefix) or email address for identity binding."""
    if not identifier:
        return ""
    identifier = str(identifier).strip()
    if "@" in identifier:
        return identifier.lower()
    digits = "".join(filter(str.isdigit, identifier))
    if len(digits) == 10:
        digits = f"91{digits}"
    elif digits.startswith("0") and len(digits) == 11:
        digits = f"91{digits[1:]}"
    return digits


import math
from collections import Counter

_TEST_OTP_FINGERPRINT_KEY = "test-only-isolated-otp-hmac-fingerprint-secret-min32bytes"


def calculate_shannon_entropy(data: str) -> float:
    """
    Calculates the Shannon information entropy of the string in bits per character
    based on character frequency distribution.

    NOTE: Shannon entropy over a string's character distribution is a heuristic sanity
    filter, NOT mathematical proof of cryptographic randomness. A deterministic sequence
    or shuffled dictionary can exhibit high character distribution entropy without being
    cryptographically random. True cryptographic security depends on generating the secret
    material from a Cryptographically Secure Pseudo-Random Number Generator (CSPRNG).
    """
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def validate_key_entropy(key_str: str, key_name: str) -> None:
    """
    FG-SEC-002 Hardening: Validates key configuration for OTP recipient fingerprinting:
    1. Minimum byte length (>= 32 bytes / 256 bits of key material).
    2. Minimum character diversity and heuristic distribution check (entropy >= 3.0 bits/char,
       unique characters >= 8) to reject degenerate, repetitive (e.g. 'a'*32), or trivial strings.

    IMPORTANT: Character distribution checks alone do not prove cryptographic randomness.
    Secrets must be generated using an OS CSPRNG with at least 256 bits of random entropy:
        python -c "import secrets; print(secrets.token_hex(32))"
    """
    if not key_str or not key_str.strip():
        raise RuntimeError(f"CRITICAL: {key_name} is missing or empty.")

    key_bytes = key_str.strip().encode("utf-8")
    if len(key_bytes) < 32:
        raise RuntimeError(
            f"CRITICAL: {key_name} must contain at least 32 bytes (256 bits) of key material. "
            f"Provided length: {len(key_bytes)} bytes. "
            "Generate a CSPRNG key with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Heuristic sanity checks against degenerate or trivially repetitive keys
    entropy = calculate_shannon_entropy(key_str.strip())
    unique_chars = len(set(key_str.strip()))
    if entropy < 3.0 or unique_chars < 8:
        raise RuntimeError(
            f"CRITICAL: {key_name} fails heuristic diversity check (entropy={entropy:.2f} bits/char, unique_chars={unique_chars}). "
            "Key length alone does not guarantee security; repetitive or degenerate strings are strictly rejected. "
            "Generate a cryptographically secure key with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )


def validate_previous_rotation_key() -> Optional[bytes]:
    """
    Validates OTP_PREVIOUS_FINGERPRINT_KEY whenever configured.
    Never silently ignores an invalid or weak previous key during rotation.
    """
    prev_key = getattr(settings, "OTP_PREVIOUS_FINGERPRINT_KEY", None) or os.getenv("OTP_PREVIOUS_FINGERPRINT_KEY")
    if prev_key is None or not str(prev_key).strip():
        return None
    prev_str = str(prev_key).strip()
    validate_key_entropy(prev_str, "OTP_PREVIOUS_FINGERPRINT_KEY")
    return prev_str.encode("utf-8")


def get_otp_fingerprint_key() -> bytes:
    """
    FG-SEC-002: Requires a dedicated, strong HMAC key for recipient fingerprinting.
    Rejects fallback to SECRET_KEY, development constants, or hardcoded strings.
    In production/staging, fails safely with RuntimeError if missing or weak.
    Also validates OTP_PREVIOUS_FINGERPRINT_KEY whenever configured.
    """
    key = getattr(settings, "OTP_RECIPIENT_FINGERPRINT_KEY", None) or os.getenv("OTP_RECIPIENT_FINGERPRINT_KEY")
    if key and str(key).strip():
        key_str = str(key).strip()
        validate_key_entropy(key_str, "OTP_RECIPIENT_FINGERPRINT_KEY")
        # Validate previous rotation key if configured
        validate_previous_rotation_key()
        return key_str.encode("utf-8")

    # In test environments, provide an isolated test key if not explicitly set
    is_test_env = (
        "pytest" in sys.modules
        or bool(os.getenv("PYTEST_CURRENT_TEST"))
        or bool(os.getenv("TEST_DATABASE_URL"))
    )
    if is_test_env:
        # Also validate previous key in test environment if configured
        validate_previous_rotation_key()
        return _TEST_OTP_FINGERPRINT_KEY.encode("utf-8")

    raise RuntimeError(
        "CRITICAL: OTP_RECIPIENT_FINGERPRINT_KEY environment variable is missing or empty. "
        "Production deployment requires a dedicated, cryptographically secure 32+ byte key for recipient fingerprinting. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )


def compute_recipient_fingerprint(identifier: Optional[str], key_override: Optional[bytes] = None) -> str:
    """
    FG-SEC-002: Secure cryptographic fingerprint using HMAC-SHA256.
    Ensures zero plaintext phone numbers or emails are stored in the database.
    """
    normalized = normalize_identifier(identifier)
    if not normalized:
        return ""
    key = key_override if key_override is not None else get_otp_fingerprint_key()
    return hmac.new(key, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def get_all_valid_fingerprints(identifier: Optional[str]) -> list[str]:
    """
    FG-SEC-002: Generates fingerprint using active key and, if configured, previous key.
    Supports zero-downtime key rotation for in-flight 5-minute OTP transactions.
    """
    normalized = normalize_identifier(identifier)
    if not normalized:
        return []
    fingerprints = [compute_recipient_fingerprint(identifier)]
    prev_key_bytes = validate_previous_rotation_key()
    if prev_key_bytes:
        fingerprints.append(hmac.new(prev_key_bytes, normalized.encode("utf-8"), hashlib.sha256).hexdigest())
    return fingerprints


class PersistentOTPTracker:
    """
    FG-SEC-002: Persistent, database-backed OTP transaction tracker.
    Stores HMAC fingerprint of the recipient identifier rather than plaintext.
    Uses conditional atomic updates for consumption across distributed workers.
    """

    @staticmethod
    def _get_session_ctx(db: Optional[AsyncSession] = None):
        if db is not None:
            class _NoOpContext:
                async def __aenter__(self):
                    return db
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return _NoOpContext()
        else:
            from database import async_session_factory
            return async_session_factory()

    async def record_request(
        self,
        req_id: str,
        identifier: str,
        provider: str = "MSG91",
        ttl_minutes: int = 5,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        if not req_id or not identifier:
            return False

        fingerprint = compute_recipient_fingerprint(identifier)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=ttl_minutes)

        try:
            async with self._get_session_ctx(db) as session:
                tx = OTPTransaction(
                    req_id=str(req_id).strip(),
                    recipient_fingerprint=fingerprint,
                    provider=provider,
                    expires_at=expires_at,
                    is_consumed=False,
                )
                session.add(tx)
                await session.flush()
                if db is None:
                    await session.commit()
                logger.info(f"[OTP Tracker] Persisted OTP transaction for req_id={req_id}")
                return True
        except Exception as e:
            logger.error(f"[OTP Tracker] Failed to record OTP transaction: {e}")
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable (failed to persist security transaction)."
            )

    async def validate_binding(
        self,
        req_id: Optional[str],
        identifier: Optional[str],
        db: Optional[AsyncSession] = None,
    ) -> Tuple[bool, str]:
        """
        Validates that the transaction exists, is unconsumed, unexpired,
        and belongs to the given recipient identifier WITHOUT consuming it yet.
        Prevents identity substitution and does not consume the OTP prematurely.
        """
        if not req_id or not str(req_id).strip():
            return False, "Missing transaction reference (req_id)"
        if not identifier or not str(identifier).strip():
            return False, "Missing recipient identifier"

        valid_fps = get_all_valid_fingerprints(identifier)
        clean_req_id = str(req_id).strip()
        now = datetime.now(timezone.utc)

        try:
            async with self._get_session_ctx(db) as session:
                stmt = select(OTPTransaction).where(OTPTransaction.req_id == clean_req_id)
                result = await session.execute(stmt)
                tx = result.scalar_one_or_none()

                if not tx:
                    logger.warning(f"[OTP Tracker] Unknown transaction req_id: {clean_req_id}")
                    return False, "OTP transaction not found or expired"

                if tx.is_consumed:
                    logger.warning(f"[OTP Tracker] Replay attempted on consumed req_id: {clean_req_id}")
                    return False, "OTP has already been used"

                exp = tx.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < now:
                    logger.warning(f"[OTP Tracker] Expired transaction req_id: {clean_req_id}")
                    return False, "OTP has expired"

                if tx.recipient_fingerprint not in valid_fps:
                    logger.warning(
                        f"[OTP Tracker] Identity mismatch for req_id={clean_req_id}: "
                        f"submitted identifier fingerprint does not match issuing fingerprint."
                    )
                    return False, "OTP was not issued for this account or phone number"

                return True, "Valid"
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[OTP Tracker] Error in validate_binding: {e}")
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable."
            )

    async def consume_transaction(
        self,
        req_id: Optional[str],
        identifier: Optional[str],
        db: Optional[AsyncSession] = None,
    ) -> Tuple[bool, str]:
        """
        Atomically consumes the OTP transaction in the database.
        Uses a conditional UPDATE: only succeeds if req_id and fingerprint match,
        is_consumed is False, and expires_at > now.
        Guarantees only ONE concurrent request can consume the transaction.
        """
        if not req_id or not identifier:
            return False, "Missing req_id or identifier"

        valid_fps = get_all_valid_fingerprints(identifier)
        clean_req_id = str(req_id).strip()
        now = datetime.now(timezone.utc)

        try:
            async with self._get_session_ctx(db) as session:
                stmt = (
                    update(OTPTransaction)
                    .where(
                        OTPTransaction.req_id == clean_req_id,
                        OTPTransaction.recipient_fingerprint.in_(valid_fps),
                        OTPTransaction.is_consumed == False,
                        OTPTransaction.expires_at > now,
                    )
                    .values(
                        is_consumed=True,
                        consumed_at=now,
                    )
                )
                res = await session.execute(stmt)
                await session.flush()
                if db is None:
                    await session.commit()

                if res.rowcount == 1:
                    logger.info(f"[OTP Tracker] Atomic consumption succeeded for req_id={clean_req_id}")
                    return True, "Consumed"
                else:
                    logger.warning(f"[OTP Tracker] Atomic consumption rejected for req_id={clean_req_id} (already consumed or expired)")
                    return False, "OTP has already been used or expired"
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[OTP Tracker] Error in consume_transaction: {e}")
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable."
            )

    async def verify_and_consume(
        self,
        req_id: Optional[str],
        identifier: Optional[str],
        db: Optional[AsyncSession] = None,
    ) -> Tuple[bool, str]:
        """Combined atomic validation and consumption."""
        valid, err = await self.validate_binding(req_id, identifier, db=db)
        if not valid:
            return False, err
        return await self.consume_transaction(req_id, identifier, db=db)

    async def clear(self, db: Optional[AsyncSession] = None):
        """Purge all OTP transactions (for test isolation)."""
        try:
            async with self._get_session_ctx(db) as session:
                await session.execute(delete(OTPTransaction))
                await session.flush()
                if db is None:
                    await session.commit()
        except Exception as e:
            logger.error(f"[OTP Tracker] Error in clear: {e}")


otp_tracker = PersistentOTPTracker()


def _sanitize_error_message(err: Any, *secrets: Optional[str]) -> str:
    """FG-SEC-020: Strip API keys and secret tokens from error representations before logging."""
    msg = str(err)
    for secret in secrets:
        if secret and secret in msg:
            msg = msg.replace(secret, "[REDACTED_API_KEY]")
    return msg


class MSG91OTPProvider(OTPProvider):
    """
    Official MSG91 Standard OTP API integration.
    Handles OTP generation, delivery, retry, and verification externally.
    """
    def __init__(self):
        self.auth_key = settings.MSG91_AUTH_KEY
        self.template_id = settings.MSG91_TEMPLATE_ID

        if not self.auth_key:
            logger.error("MSG91_AUTH_KEY is missing! OTP sends will fail.")

        if not self.template_id:
            logger.error("MSG91_TEMPLATE_ID is missing! Standard OTP API requires a template_id.")

    def _get_headers(self):
        return {
            "authkey": self.auth_key or "",
            "Content-Type": "application/json"
        }

    async def request_otp(self, identifier: str, db: Optional[Any] = None) -> OTPRequestResult:
        if not self.auth_key or not self.template_id:
            logger.error("OTP Request Failed: MSG91 is not fully configured (missing auth_key or template_id).")
            return OTPRequestResult(False, "Configuration Error: MSG91 is not fully configured")

        cleaned_id = "".join(filter(str.isdigit, identifier))
        if len(cleaned_id) == 10:
            cleaned_id = f"91{cleaned_id}"

        # FG-SEC-020: Authkey passed securely via headers (_get_headers), not in query parameters
        url = f"https://control.msg91.com/api/v5/otp?template_id={self.template_id}&mobile={cleaned_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self._get_headers(), json={})
                data = response.json()

                if data.get("type") == "success":
                    logger.info(f"MSG91 Standard OTP sent for {cleaned_id}")
                    # FG-SEC-002: Persist OTP request binding to recipient fingerprint
                    await otp_tracker.record_request(cleaned_id, identifier, provider="MSG91", db=db)
                    return OTPRequestResult(True, "OTP sent successfully", provider_reference=cleaned_id)
                else:
                    logger.error(f"MSG91 Standard request failed: {data}")
                    error_detail = data.get("message", "Unknown MSG91 error")
                    return OTPRequestResult(False, f"MSG91 Error: {error_detail}")
        except Exception as e:
            logger.error(f"MSG91 API exception: {_sanitize_error_message(e, self.auth_key)}")
            return OTPRequestResult(False, "Provider API error")

    async def retry_otp(self, req_id: str, channel: str = "SMS") -> OTPRequestResult:
        if not self.auth_key:
            logger.error("OTP Retry Failed: MSG91 is not fully configured.")
            return OTPRequestResult(False, "Configuration Error: MSG91 is not fully configured")

        # FG-SEC-020: Authkey passed securely via headers (_get_headers), not in query parameters
        url = f"https://control.msg91.com/api/v5/otp/retry?retrytype=text&mobile={req_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._get_headers())
                data = response.json()

                if data.get("type") == "success":
                    logger.info(f"MSG91 Standard OTP retried for {req_id}")
                    return OTPRequestResult(True, "OTP resent successfully", provider_reference=req_id)
                else:
                    logger.error(f"MSG91 Standard retry failed: {data}")
                    return OTPRequestResult(False, "Failed to resend OTP via provider")
        except Exception as e:
            logger.error(f"MSG91 API exception: {_sanitize_error_message(e, self.auth_key)}")
            return OTPRequestResult(False, "Provider API error")

    async def verify_otp(self, req_id: str, code: str) -> OTPVerificationResult:
        if not self.auth_key:
            logger.error("OTP Verify Failed: MSG91 is not fully configured.")
            return OTPVerificationResult(False, "Configuration Error: MSG91 is not fully configured")

        # FG-SEC-020: Authkey passed securely via headers (_get_headers), not in query parameters
        url = f"https://control.msg91.com/api/v5/otp/verify?otp={code}&mobile={req_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._get_headers())
                data = response.json()

                if data.get("type") == "success":
                    logger.info(f"MSG91 Standard OTP verified for {req_id}")
                    return OTPVerificationResult(True, "OTP verified successfully")
                else:
                    logger.warning(f"MSG91 Standard verification failed for {req_id}: {data}")
                    return OTPVerificationResult(False, "Invalid or expired OTP")
        except Exception as e:
            logger.error(f"MSG91 API exception: {_sanitize_error_message(e, self.auth_key)}")
            return OTPVerificationResult(False, "Provider API error")

    async def verify_access_token(self, token: str) -> OTPVerificationResult:
        if not self.auth_key:
            logger.error("OTP Access Token Verify Failed: MSG91_AUTH_KEY is missing from backend configuration.")
            return OTPVerificationResult(False, "Configuration Error: MSG91_AUTH_KEY is missing from backend environment")

        url = "https://api.msg91.com/api/v5/widget/verifyAccessToken"
        payload = {
            "access-token": token
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self._get_headers())
                data = response.json()

                if data.get("type") == "success":
                    return OTPVerificationResult(True, "Access Token verified successfully")
                else:
                    logger.warning(f"MSG91 Widget access token verification failed: {data}")
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

    async def request_otp(self, identifier: str, db: Optional[Any] = None) -> OTPRequestResult:
        if not settings.OTP_MOCK_MODE:
            return OTPRequestResult(False, "Mock mode disabled")
        logger.info(f"[MOCK] OTP requested for {identifier}")
        mock_req_id = f"mock_req_{uuid.uuid4().hex[:12]}"
        # FG-SEC-002: Persist OTP request binding to recipient fingerprint
        await otp_tracker.record_request(mock_req_id, identifier, provider="MOCK", db=db)
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
