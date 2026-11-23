"""
FleetGuard — Field-Level Cryptographic Encryption & Blind Indexing (FG-SEC-030)

Provides transparent AES-256-GCM authenticated encryption for sensitive PII
(Aadhaar, driver license numbers, bank account details) stored in PostgreSQL,
along with HMAC-SHA256 blind indexing for deterministic exact-match querying.
"""

import os
import base64
import hmac
import hashlib
import secrets
from typing import Optional, Any
from sqlalchemy.types import TypeDecorator, String
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import settings

ENCRYPTION_PREFIX = "enc:v1:"
NONCE_LENGTH = 12  # Standard 96-bit nonce for AES-GCM
KEY_LENGTH = 32    # 256-bit key

_cached_aesgcm: Optional[AESGCM] = None
_cached_key_bytes: Optional[bytes] = None


def get_encryption_key_bytes() -> bytes:
    """
    Retrieve and validate the 256-bit field encryption key from settings.
    In testing or debug mode, provides a fallback development key if unset.
    In production, fails closed if the key is missing or invalid.
    """
    key_str = getattr(settings, "FIELD_ENCRYPTION_KEY", None)

    if not key_str:
        if settings.DEBUG or os.environ.get("OTP_MOCK_MODE") == "True" or os.environ.get("TESTING") == "True":
            # Development fallback key (never used in production)
            return b"fleetguard_field_encrypt_32bytes"
        raise ValueError(
            "CRITICAL SECURITY CONFIGURATION: FIELD_ENCRYPTION_KEY must be set in production. "
            "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )

    # Decode hex key if 64 chars hex string, else raw utf-8
    try:
        if len(key_str) == 64:
            key_bytes = bytes.fromhex(key_str)
        else:
            key_bytes = key_str.encode("utf-8")
    except Exception as e:
        raise ValueError(f"Invalid FIELD_ENCRYPTION_KEY format: {e}")

    if len(key_bytes) < KEY_LENGTH:
        raise ValueError(
            f"FIELD_ENCRYPTION_KEY must provide at least {KEY_LENGTH} bytes of key material "
            f"(got {len(key_bytes)} bytes)."
        )

    return key_bytes[:KEY_LENGTH]


def _get_aesgcm() -> AESGCM:
    global _cached_aesgcm, _cached_key_bytes
    key_bytes = get_encryption_key_bytes()
    if _cached_aesgcm is None or _cached_key_bytes != key_bytes:
        _cached_aesgcm = AESGCM(key_bytes)
        _cached_key_bytes = key_bytes
    return _cached_aesgcm


def encrypt_field(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypt a plaintext string using AES-256-GCM.
    Returns format: 'enc:v1:<base64(12-byte-nonce + ciphertext + 16-byte-tag)>'.
    """
    if plaintext is None or plaintext == "":
        return plaintext

    # If already encrypted, return as is
    if plaintext.startswith(ENCRYPTION_PREFIX):
        return plaintext

    aesgcm = _get_aesgcm()
    nonce = secrets.token_bytes(NONCE_LENGTH)
    ciphertext_and_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext_and_tag
    encoded = base64.b64encode(payload).decode("ascii")
    return f"{ENCRYPTION_PREFIX}{encoded}"


def decrypt_field(stored_value: Optional[str]) -> Optional[str]:
    """
    Decrypt an AES-256-GCM encrypted field envelope.
    If the value does not have the 'enc:v1:' prefix, it is returned as plaintext
    to provide zero-downtime backward compatibility for pre-existing records.
    """
    if stored_value is None or stored_value == "":
        return stored_value

    if not stored_value.startswith(ENCRYPTION_PREFIX):
        # Legacy unencrypted record
        return stored_value

    b64_payload = stored_value[len(ENCRYPTION_PREFIX):]
    try:
        payload = base64.b64decode(b64_payload)
        if len(payload) <= NONCE_LENGTH + 16:
            raise ValueError("Payload too short for AES-GCM envelope")

        nonce = payload[:NONCE_LENGTH]
        ciphertext_and_tag = payload[NONCE_LENGTH:]
        aesgcm = _get_aesgcm()
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext_and_tag, None)
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Field decryption failed or invalid MAC: {e}")


def generate_blind_index(value: Optional[str], salt: Optional[str] = None) -> Optional[str]:
    """
    Generate a deterministic HMAC-SHA256 blind index for exact equality queries.
    Allows exact searching on encrypted fields without leaking the plaintext.
    """
    if value is None or value == "":
        return None

    # Normalize value: strip whitespace and uppercase for case-insensitive indexing
    normalized = value.strip().upper()
    key_bytes = get_encryption_key_bytes()
    salt_bytes = (salt or "fleetguard_blind_index").encode("utf-8")
    derived_key = hashlib.sha256(key_bytes + salt_bytes).digest()

    return hmac.new(derived_key, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that transparently encrypts strings on flush
    and decrypts them on load using AES-256-GCM.
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect: Any) -> Optional[str]:
        if value is None:
            return None
        return encrypt_field(str(value))

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        if value is None:
            return None
        return decrypt_field(value)
