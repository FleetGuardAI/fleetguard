import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from models.vehicle_domain import Vehicle

logger = logging.getLogger("fleetguard.odometer_service")


class OdometerService:
    # Plausibility limits for commercial vehicle fleet operations
    MAX_SPEED_KMH = 150.0               # Maximum realistic highway speed in km/h
    MAX_UNREASONABLE_DELTA_KM = 5000.0  # Absolute single jump threshold requiring admin override
    MAX_INITIAL_ODOMETER_KM = 2000000.0 # 2 million km max initial reading

    @classmethod
    def is_plausible_odometer_delta(
        cls,
        current_odometer: Optional[float],
        new_odometer: float,
        last_update_at: Optional[datetime],
        new_timestamp: datetime,
        admin_override: bool = False,
    ) -> Tuple[bool, str]:
        """
        FG-SEC-017: Validates whether the delta between current and new odometer is physically plausible.
        Prevents unbounded driver inputs (e.g. 999,999,999 km) from causing permanent vehicle lockout.
        Returns (is_valid, reason).
        """
        if new_odometer is None or new_odometer < 0:
            return False, "Negative or null odometer reading"

        if current_odometer is None:
            if new_odometer > cls.MAX_INITIAL_ODOMETER_KM and not admin_override:
                return False, f"Initial odometer reading {new_odometer:,.0f} km exceeds limit ({cls.MAX_INITIAL_ODOMETER_KM:,.0f} km) without admin override"
            return True, "Initial reading accepted"

        delta_km = new_odometer - current_odometer
        if delta_km < 0:
            return False, f"Odometer rollback not permitted ({current_odometer} -> {new_odometer})"

        if admin_override:
            return True, "Admin override accepted"

        # Check maximum single jump cap (e.g. 5,000 km)
        if delta_km > cls.MAX_UNREASONABLE_DELTA_KM:
            return False, (
                f"Odometer jump of {delta_km:,.1f} km exceeds maximum plausible single jump "
                f"({cls.MAX_UNREASONABLE_DELTA_KM:,.0f} km) without admin override"
            )

        # Check speed plausibility if timestamps are available
        if last_update_at and new_timestamp:
            # Normalize timezones
            t_last = last_update_at if last_update_at.tzinfo else last_update_at.replace(tzinfo=timezone.utc)
            t_new = new_timestamp if new_timestamp.tzinfo else new_timestamp.replace(tzinfo=timezone.utc)
            elapsed_seconds = (t_new - t_last).total_seconds()
            if elapsed_seconds > 0:
                elapsed_hours = elapsed_seconds / 3600.0
                speed_kmh = delta_km / elapsed_hours
                # Only enforce speed cap if delta is substantial (> 50 km) to allow minor odometer calibration
                if speed_kmh > cls.MAX_SPEED_KMH and delta_km > 50.0:
                    return False, (
                        f"Implausible speed {speed_kmh:,.1f} km/h (delta: {delta_km:,.1f} km "
                        f"in {elapsed_hours:.2f} hours, limit is {cls.MAX_SPEED_KMH} km/h)"
                    )
            elif elapsed_seconds < 0:
                return False, f"Stale odometer reading: timestamp {new_timestamp} is older than last update {last_update_at}"

        return True, "Plausible reading"

    @classmethod
    def validate_odometer_reading(
        cls,
        vehicle: Vehicle,
        new_odometer: float,
        timestamp: datetime,
        admin_override: bool = False,
    ) -> None:
        """
        Validates the odometer reading and raises ValueError if invalid.
        """
        valid, reason = cls.is_plausible_odometer_delta(
            current_odometer=vehicle.current_odometer,
            new_odometer=new_odometer,
            last_update_at=vehicle.last_odometer_update_at,
            new_timestamp=timestamp,
            admin_override=admin_override,
        )
        if not valid:
            raise ValueError(reason)

    @classmethod
    def update_odometer_if_valid(
        cls,
        vehicle: Vehicle,
        new_odometer: float,
        timestamp: datetime,
        admin_override: bool = False,
    ) -> bool:
        """
        Updates the vehicle's current odometer if the reading is valid, newer, and physically plausible.
        Returns True if updated, False otherwise.
        """
        valid, reason = cls.is_plausible_odometer_delta(
            current_odometer=vehicle.current_odometer,
            new_odometer=new_odometer,
            last_update_at=vehicle.last_odometer_update_at,
            new_timestamp=timestamp,
            admin_override=admin_override,
        )
        if not valid:
            logger.warning(f"Ignoring odometer update for vehicle {vehicle.id}: {reason}")
            return False

        vehicle.current_odometer = new_odometer
        vehicle.last_odometer_update_at = timestamp
        return True
