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
    DEBUG: bool = False

    # --- Database ---
    # Default to SQLite for zero-config local dev. Switch to PostgreSQL for prod:
    # DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/fleetguard
    DATABASE_URL: str = "sqlite+aiosqlite:///./fleetguard.db"

    # --- OpenAI (for receipt OCR via Vision API) ---
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    LLM_BASE_URL: Optional[str] = None



    # --- Validation Pipeline ---
    KAFKA_VALIDATION_RESULTS_TOPIC: str = "fleetguard.validation.results"
    
    # Outbox Pattern
    OUTBOX_POLL_INTERVAL_MS: int = 2000
    OUTBOX_BATCH_SIZE: int = 50

    # -----------------------------------------------------------------------
    # --- CORS ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5174",
        "https://fleetguard-delta.vercel.app",
        "https://fleetguard-git-main-rudra810s-projects.vercel.app"
    ]

    # --- Fuel Theft & Anomaly Detection Thresholds ---
    FUEL_DROP_THRESHOLD_LITERS: float = 5.0
    FUEL_DROP_WINDOW_MINUTES: int = 5
    EMA_ALPHA: float = 0.3  # Smoothing factor for Exponential Moving Average
    FUEL_ANOMALY_WARNING_THRESHOLD: float = 10.0
    FUEL_ANOMALY_CRITICAL_THRESHOLD: float = 20.0

    # --- Fair Price Risk Threshold ---
    FAIR_PRICE_OVERAGE_PERCENT: float = 20.0

    # --- JWT Authentication ---
    # IMPORTANT: Override SECRET_KEY with a strong random value in production.
    # Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REMEMBER_ME_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30



    # In DEBUG this can help local testing of forgot-password without SMS/email integration.
    # --- MSG91 OTP ---
    MSG91_AUTH_KEY: Optional[str] = None
    MSG91_WIDGET_ID: Optional[str] = None
    MSG91_WIDGET_TOKEN: Optional[str] = None
    OTP_PROVIDER: str = "MSG91"
    OTP_MOCK_MODE: bool = False
    PASSWORD_RESET_DEBUG_RETURN_TOKEN: bool = True

    # --- Kafka (Event Bus) ---
    KAFKA_ENABLED: bool = False
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: str | None = None
    KAFKA_SASL_USERNAME: str | None = None
    KAFKA_SASL_PASSWORD: str | None = None
    KAFKA_OPERATIONAL_EVENTS_TOPIC: str = "operational-events"
    
    # --- Dead Letter Queue (DLQ) ---
    DLQ_TOPIC_NAME: str = "fleetguard.dlq"
    DLQ_INCLUDE_STACK_TRACE: bool = True

    # --- Supabase Storage ---
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_STORAGE_BUCKET: str = "fleetguard-uploads"


settings = Settings()
