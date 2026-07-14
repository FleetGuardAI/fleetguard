"""
FleetGuard — Security & JWT Utilities

Reusable functions for password hashing, password verification, and JWT encoding/decoding.
Independent of FastAPI, HTTP exceptions, and database models.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import jwt
from passlib.context import CryptContext

from config import settings

# Configure password hashing context using bcrypt
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def dummy_verify() -> None:
    """
    Perform a dummy verify to simulate a password check workload.
    Helps prevent timing-attack user-enumeration.
    """
    _pwd_context.dummy_verify()


def hash_password(plain: str) -> str:

    """
    Hash a plain text password using bcrypt.

    Returns the secure password hash string.
    """
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain text password against its bcrypt hash in constant time.

    Returns True if valid, False otherwise.
    """
    return _pwd_context.verify(plain, hashed)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Encode and return a signed JWT access token.

    Defaults to `settings.ACCESS_TOKEN_EXPIRE_MINUTES` if `expires_delta` is not provided.
    """
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz=timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT access token using settings.

    Returns the decoded claims dictionary. Raises `JWTError` on validation or expiration failure.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
