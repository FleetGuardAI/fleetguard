"""
FleetGuard — OTP Service

Demo mode: accepts fixed OTP 123456.
Production: plug in Twilio, MSG91, or any SMS provider.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from config import settings

logger = logging.getLogger("fleetguard.otp")

# In-memory OTP store (demo). Production: use Redis.
_otp_store: Dict[str, Tuple[str, datetime]] = {}

# Demo mode OTP
DEMO_OTP = "123456"


class OTPService:
    """
    OTP generation and verification service.

    Demo mode: always accepts 123456.
    Production: integrate SMS provider (Twilio, MSG91, etc.)
    """

    @staticmethod
    async def send_otp(phone_number: str) -> bool:
        """
        Generate and 'send' OTP to the given phone number.

        Returns True if OTP was generated/sent successfully.
        """
        otp_code = DEMO_OTP if getattr(settings, 'DEBUG', True) else _generate_otp()
        expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=5)

        # Store OTP
        _otp_store[phone_number] = (otp_code, expires_at)

        if getattr(settings, 'DEBUG', True):
            logger.info(f"[DEMO] OTP for {phone_number}: {otp_code}")
        else:
            # Production: call SMS API
            await _send_sms(phone_number, otp_code)

        return True

    @staticmethod
    async def verify_otp(phone_number: str, otp_code: str) -> bool:
        """
        Verify OTP code for the given phone number.

        Returns True if valid and not expired.
        """
        # Demo mode: accept fixed OTP
        if getattr(settings, 'DEBUG', True) and otp_code == DEMO_OTP:
            _otp_store.pop(phone_number, None)
            logger.info(f"[DEMO] OTP verified for {phone_number}")
            return True

        stored = _otp_store.get(phone_number)
        if stored is None:
            return False

        stored_otp, expires_at = stored
        now = datetime.now(tz=timezone.utc)

        if now > expires_at:
            _otp_store.pop(phone_number, None)
            logger.warning(f"OTP expired for {phone_number}")
            return False

        if stored_otp != otp_code:
            return False

        # Clean up used OTP
        _otp_store.pop(phone_number, None)
        logger.info(f"OTP verified for {phone_number}")
        return True


def _generate_otp() -> str:
    """Generate a cryptographically secure 6-digit OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


async def _send_sms(phone_number: str, otp_code: str) -> None:
    """
    SMS provider integration point.

    Replace this function body with your chosen SMS provider:
    - Twilio: client.messages.create(...)
    - MSG91: httpx POST to MSG91 API
    - AWS SNS: boto3 sns.publish(...)
    """
    logger.info(f"SMS OTP sent to {phone_number} (provider: stub)")
    # raise NotImplementedError("Configure SMS provider in production")


# Singleton
otp_service = OTPService()
