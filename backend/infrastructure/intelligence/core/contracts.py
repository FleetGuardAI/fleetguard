from typing import Protocol, TypeVar, Generic, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import enum

class Direction(str, enum.Enum):
    DEGRADATION = "DEGRADATION"
    IMPROVEMENT = "IMPROVEMENT"
    NORMAL = "NORMAL"

class Severity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    NORMAL = "NORMAL"

class Status(str, enum.Enum):
    ANOMALY = "ANOMALY"
    NORMAL = "NORMAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

@dataclass
class MetricObservation:
    """
    A generic representation of a single metric observation.
    Independent of SQLAlchemy models.
    """
    entity_id: str
    entity_type: str
    metric_type: str
    value: float
    unit: str
    period_start: datetime
    period_end: datetime
    # We allow generic strings for these so we don't depend on FuelSource/DataQuality enums
    source: str
    quality: str
    measurement_type: str
    source_reference: Optional[str] = None
    observation_id: Optional[str] = None

class DirectionStrategy(Protocol):
    def evaluate_direction(self, deviation_percent: float) -> Direction:
        """
        Determines if a deviation constitutes an improvement, degradation, or normal behavior.
        E.g., +10% duration is DEGRADATION, but +10% efficiency is IMPROVEMENT.
        """
        ...

class SeverityStrategy(Protocol):
    def evaluate_severity(self, deviation_percent: float) -> tuple[Severity, Status]:
        """
        Determines the severity and final status based on the deviation.
        Returns a tuple of (Severity, Status).
        """
        ...
