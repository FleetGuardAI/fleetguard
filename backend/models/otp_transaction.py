"""
FleetGuard — OTP Transaction ORM Model
FG-SEC-002: Persistent, distributed OTP transaction store.
Guarantees recipient binding, single-use consumption, atomic updates across instances,
and prevents replay attacks and server-restart state loss.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class OTPTransaction(Base):
    """
    Persistent OTP transaction record.
    Stores cryptographic HMAC fingerprint of the recipient identifier rather than plaintext.
    """
    __tablename__ = "otp_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    req_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    recipient_fingerprint: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="MSG91")

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
