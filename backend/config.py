"""
FleetGuard — Application Configuration
Loads settings from environment variables / .env file using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, Any, List

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
    # PostgreSQL (production):
    # DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/fleetguard
    DATABASE_URL: str

    # --- OpenAI (for receipt OCR via Vision API) ---
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    LLM_BASE_URL: Optional[str] = None
    OCR_PROVIDER: str = "ocr_space"
    OCR_SPACE_API_KEY: Optional[str] = None
    # --- AI Co-Pilot ---
    COPILOT_MAX_CONTEXT_MESSAGES: int = 20
    COPILOT_MAX_CONTEXT_TOKENS: int = 4000
    COPILOT_ENABLE_SUMMARIZATION: bool = True
    COPILOT_MAX_SUMMARY_TOKENS: int = 250

    # --- Fleet Intelligence Engine ---
    INTELLIGENCE_GPS_STALE_MINUTES: int = 15
    INTELLIGENCE_GPS_UNAVAILABLE_HOURS: int = 24
    INTELLIGENCE_MAINTENANCE_DUE_SOON_DAYS: int = 7
    INTELLIGENCE_MAINTENANCE_DUE_SOON_KM: float = 500.0
    INTELLIGENCE_TRIP_DELAY_THRESHOLD_HOURS: float = 2.0
    INTELLIGENCE_TRIP_DISTANCE_DEVIATION_PCT: float = 15.0
    INTELLIGENCE_FUEL_ANOMALY_DEVIATION_PCT: float = 20.0

    # --- Maps & Routing ---
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    GEOAPIFY_API_KEY: Optional[str] = None
    ROUTING_PROVIDER: str = "google"   # "google", "geoapify", "manual"
    LOCATION_PROVIDER: str = "google"  # "google", "geoapify", "none"
    ROUTE_CACHE_TTL_SECONDS: int = 3600
    DEFAULT_TOLL_RATE_PER_KM: float = 2.5  # Fallback if tolls not available

    # --- Validation Pipeline ---
    KAFKA_VALIDATION_RESULTS_TOPIC: str = "fleetguard.validation.results"
    
    # Outbox Pattern
    OUTBOX_POLL_INTERVAL_MS: int = 2000
    OUTBOX_BATCH_SIZE: int = 50

    # -----------------------------------------------------------------------
    # --- CORS ---
    CORS_ORIGINS: list[str] = [
        "https://super-admin-seven-sepia.vercel.app",
        "https://fleetguard-delta.vercel.app",
        "https://fleetgaurd-delta.vercel.app",
        "https://fleetguard-git-main-rudra810s-projects.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                import json
                try:
                    origins = json.loads(v_stripped)
                except Exception:
                    origins = [x.strip() for x in v_stripped.strip("[]").split(",")]
            else:
                origins = [x.strip() for x in v_stripped.split(",") if x.strip()]
        elif isinstance(v, (list, tuple, set)):
            origins = list(v)
        else:
            origins = []

        default_origins = [
            "https://super-admin-seven-sepia.vercel.app",
            "https://fleetguard-delta.vercel.app",
            "https://fleetgaurd-delta.vercel.app",
            "https://fleetguard-git-main-rudra810s-projects.vercel.app",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:3000",
        ]

        normalized: list[str] = []
        for origin in list(origins) + default_origins:
            if origin:
                cleaned = str(origin).strip().rstrip("/")
                if cleaned and cleaned not in normalized:
                    normalized.append(cleaned)
        return normalized


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
    MSG91_TEMPLATE_ID: Optional[str] = None
    MSG91_WIDGET_ID: Optional[str] = None
    MSG91_WIDGET_TOKEN: Optional[str] = None
    OTP_PROVIDER: str = "MSG91"
    OTP_MOCK_MODE: bool = False
    PASSWORD_RESET_DEBUG_RETURN_TOKEN: bool = False

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

    # --- Redis Caching ---
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    SUPABASE_STORAGE_BUCKET: str = "fleetguard-uploads"


settings = Settings()
