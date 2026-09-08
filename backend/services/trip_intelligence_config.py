"""
FleetGuard — Trip Intelligence Configuration

Centralized, configurable business rules for Trip Intelligence.
All thresholds and defaults are in one place — no scattered hardcoded values.

Architecture supports future per-tenant DB override via company settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass(frozen=True)
class TripIntelligenceConfig:
    """
    Central configuration for Trip Intelligence calculations.
    Loaded from environment variables with sensible defaults.

    These are NOT permanent hardcoded rules — they are configurable defaults
    that support future per-tenant override.
    """

    # ── Decision Thresholds ──────────────────────────────────────
    # Margin >= take_margin_pct → TAKE (if other factors allow)
    # review_margin_pct <= margin < take_margin_pct → REVIEW
    # margin < review_margin_pct → AVOID
    take_margin_pct: float = 15.0
    review_margin_pct: float = 5.0

    # Target margin for minimum freight calculation
    target_margin_pct: float = 10.0

    # ── Cost Assumption Defaults (clearly labelled) ──────────────
    # System default fuel efficiency — used ONLY when no historical data
    default_fuel_efficiency_kmpl: float = 4.0

    # System default fuel price — used ONLY when no expense-derived price
    default_fuel_price_per_liter: float = 100.0

    # Economics 2.0 defaults
    default_toll_rate_per_km: float = 2.5
    default_operating_cost_per_km: float = 5.0
    default_driver_cost_per_day: float = 1500.0

    # Average speed assumption (km/h) for duration estimation
    default_avg_speed_kmph: float = 45.0

    # ── Anomaly Detection Thresholds ─────────────────────────────
    fuel_variance_warning_pct: float = 8.0
    fuel_variance_critical_pct: float = 15.0
    duration_variance_warning_pct: float = 15.0
    duration_variance_critical_pct: float = 30.0
    distance_variance_warning_pct: float = 10.0
    expense_variance_warning_pct: float = 15.0
    cost_variance_warning_pct: float = 10.0

    # ── Live Trip Health Thresholds ──────────────────────────────
    # Profit erosion percentage thresholds
    profit_erosion_warning_pct: float = 20.0   # AT_RISK
    profit_erosion_critical_pct: float = 50.0  # CRITICAL

    # ── Intelligence Versioning ──────────────────────────────────
    intelligence_version: str = "trip-intelligence-v1"

    # ── Minimum Data Requirements ────────────────────────────────
    # Minimum historical trips for "HIGH" confidence vehicle efficiency
    min_trips_for_high_confidence: int = 5
    min_trips_for_medium_confidence: int = 2


def load_intelligence_config() -> TripIntelligenceConfig:
    """
    Load Trip Intelligence configuration from environment variables.
    Falls back to dataclass defaults if not set.
    """
    def _float(key: str, default: float) -> float:
        val = os.environ.get(key)
        if val:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return default

    def _int(key: str, default: int) -> int:
        val = os.environ.get(key)
        if val:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
        return default

    def _str(key: str, default: str) -> str:
        return os.environ.get(key, default)

    return TripIntelligenceConfig(
        take_margin_pct=_float("TI_TAKE_MARGIN_PCT", 15.0),
        review_margin_pct=_float("TI_REVIEW_MARGIN_PCT", 5.0),
        target_margin_pct=_float("TI_TARGET_MARGIN_PCT", 10.0),
        default_fuel_efficiency_kmpl=_float("TI_DEFAULT_FUEL_EFFICIENCY_KMPL", 4.0),
        default_fuel_price_per_liter=_float("TI_DEFAULT_FUEL_PRICE_PER_LITER", 100.0),
        default_driver_cost_per_day=_float("TI_DEFAULT_DRIVER_COST_PER_DAY", 1500.0),
        default_avg_speed_kmph=_float("TI_DEFAULT_AVG_SPEED_KMPH", 45.0),
        profit_erosion_warning_pct=_float("TI_PROFIT_EROSION_WARNING_PCT", 20.0),
        profit_erosion_critical_pct=_float("TI_PROFIT_EROSION_CRITICAL_PCT", 50.0),
        intelligence_version=_str("TI_INTELLIGENCE_VERSION", "trip-intelligence-v1"),
        min_trips_for_high_confidence=_int("TI_MIN_TRIPS_HIGH_CONFIDENCE", 5),
        min_trips_for_medium_confidence=_int("TI_MIN_TRIPS_MEDIUM_CONFIDENCE", 2),
    )


# Module-level singleton — imported by services
intelligence_config = load_intelligence_config()
