import math
from typing import Tuple, Optional
from infrastructure.intelligence.core.contracts import DirectionStrategy, SeverityStrategy, Direction, Severity, Status

class GenericAnomalyEngine:
    """
    Generic mathematical engine for detecting anomalies based on deviations from baselines.
    Operates independently of any domain knowledge, relying on injected strategies.
    """
    
    def evaluate(
        self,
        observed_value: float,
        baseline_value: float,
        direction_strategy: DirectionStrategy,
        severity_strategy: SeverityStrategy
    ) -> Tuple[Optional[float], Direction, Severity, Status]:
        """
        Calculates deviation and delegates to strategies to determine semantics.
        Returns: (deviation_percent, Direction, Severity, Status)
        """
        if baseline_value is None or baseline_value == 0:
            return None, Direction.NORMAL, Severity.NORMAL, Status.INSUFFICIENT_DATA
            
        if not math.isfinite(observed_value) or not math.isfinite(baseline_value):
            return None, Direction.NORMAL, Severity.NORMAL, Status.INSUFFICIENT_DATA
            
        # (current - baseline) / baseline * 100
        # Round to 4 decimal places exactly as V1 does
        deviation_percent = round(((observed_value - baseline_value) / baseline_value) * 100.0, 4)
        
        direction = direction_strategy.evaluate_direction(deviation_percent)
        severity, status = severity_strategy.evaluate_severity(deviation_percent)
        
        # Ensure IMPROVEMENT is always normal severity and status
        if direction == Direction.IMPROVEMENT:
            severity = Severity.NORMAL
            status = Status.NORMAL
            
        return deviation_percent, direction, severity, status
