"""
FleetGuard — Application Configuration
Loads settings from environment variables / .env file using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Central configuration for the FleetGuard backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "FleetGuard TMS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- Database ---
    # Default to SQLite for zero-config local dev. Switch to PostgreSQL for prod:
    # DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/fleetguard
    DATABASE_URL: str = "sqlite+aiosqlite:///./fleetguard.db"

    # --- OpenAI (for receipt OCR via Vision API) ---
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"

    # --- WhatsApp Business API ---
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v21.0"
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "fleetguard_webhook_verify_2026"

    # --- CORS ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # --- Fuel Theft Detection Thresholds ---
    FUEL_DROP_THRESHOLD_LITERS: float = 5.0
    FUEL_DROP_WINDOW_MINUTES: int = 5
    EMA_ALPHA: float = 0.3  # Smoothing factor for Exponential Moving Average

    # --- Fair Price Risk Threshold ---
    FAIR_PRICE_OVERAGE_PERCENT: float = 20.0

    # --- JWT Authentication ---
    # IMPORTANT: Override SECRET_KEY with a strong random value in production.
    # Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "change-me-in-production-use-a-strong-random-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours



settings = Settings()
