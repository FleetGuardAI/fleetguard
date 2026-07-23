"""
Vehicle Management Domain - Validators
"""

from datetime import datetime, timezone
from typing import Optional
from domain.vehicle.errors import InvalidVehicleState
from domain.vehicle.models import Vehicle

def validate_manufacturing_year(year: int) -> None:
    current_year = datetime.now(timezone.utc).year
    if year < 1950 or year > current_year + 1:
        raise InvalidVehicleState(f"Manufacturing year {year} is out of bounds.")
