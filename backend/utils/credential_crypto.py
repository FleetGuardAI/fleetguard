"""
FleetGuard / Vahan — Credential Cryptography Utility
Provides secure, tamper-evident symmetric encryption for sensitive hardware credentials
(API keys, device passwords, MQTT passwords, webhook secrets).
Uses AES-128-CBC with HMAC-SHA256 (Fernet) keyed from SECRET_KEY.
"""

import base64
import hashlib
import json
from typing import Any, Optional
from cryptography.fernet import Fernet, InvalidToken
from config import settings


def _get_fernet_key() -> bytes:
    """
    Derives a standard 32-byte URL-safe base64-encoded key for Fernet
    from the application's SECRET_KEY using SHA-256.
    """
    secret = settings.SECRET_KEY or "fallback-secret-key-change-in-production-32b"
    key_32 = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_32)


def encrypt_credential(plain_text: Optional[str]) -> Optional[str]:
    """
    Encrypts a sensitive plaintext string.
    Returns ciphertext string or None if input is empty.
    """
    if not plain_text:
        return None
    fernet = Fernet(_get_fernet_key())
    encrypted = fernet.encrypt(plain_text.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_credential(cipher_text: Optional[str]) -> Optional[str]:
    """
    Decrypts a ciphertext string.
    Returns plaintext string or None if input is empty or invalid.
    """
    if not cipher_text:
        return None
    try:
        fernet = Fernet(_get_fernet_key())
        decrypted = fernet.decrypt(cipher_text.encode("utf-8"))
        return decrypted.decode("utf-8")
    except (InvalidToken, Exception):
        return None


def encrypt_dict(data: Optional[dict[str, Any]]) -> Optional[str]:
    """Serializes and encrypts a dictionary of credentials."""
    if not data:
        return None
    json_str = json.dumps(data)
    return encrypt_credential(json_str)


def decrypt_dict(cipher_text: Optional[str]) -> dict[str, Any]:
    """Decrypts and deserializes a dictionary of credentials."""
    plain = decrypt_credential(cipher_text)
    if not plain:
        return {}
    try:
        return json.loads(plain)
    except Exception:
        return {}
