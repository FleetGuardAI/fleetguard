"""
Trip Management Domain - Validators
"""

from domain.trip.models import TripStatus
from domain.trip.errors import InvalidTripState, ImmutableTripError

def validate_state_transition(current: TripStatus, target: TripStatus) -> None:
    if current in (TripStatus.COMPLETED, TripStatus.CANCELLED):
        raise ImmutableTripError(f"Cannot transition from terminal state {current}")
        
    valid_transitions = {
        TripStatus.CREATED: [TripStatus.IN_PROGRESS, TripStatus.CANCELLED],
        TripStatus.IN_PROGRESS: [TripStatus.PAUSED, TripStatus.COMPLETED, TripStatus.CANCELLED],
        TripStatus.PAUSED: [TripStatus.IN_PROGRESS, TripStatus.COMPLETED, TripStatus.CANCELLED]
    }
    
    if target not in valid_transitions.get(current, []):
        raise InvalidTripState(f"Invalid transition from {current} to {target}")
