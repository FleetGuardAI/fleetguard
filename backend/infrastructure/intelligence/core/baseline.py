import statistics
import math
from typing import List, Optional
from infrastructure.intelligence.core.contracts import MetricObservation

class GenericBaselineEngine:
    """
    Generic mathematical engine for calculating baselines.
    Operates solely on MetricObservation contracts without any database or domain knowledge.
    """
    
    def calculate_median(self, observations: List[MetricObservation], min_samples: int = 5) -> Optional[float]:
        """
        Calculates the median value from a list of valid observations.
        Returns None if there are insufficient valid observations.
        """
        valid_observations = self._filter_mathematically_valid(observations)
        
        if len(valid_observations) < min_samples:
            return None
            
        values = [obs.value for obs in valid_observations]
        return statistics.median(values)
        
    def _filter_mathematically_valid(self, observations: List[MetricObservation]) -> List[MetricObservation]:
        """
        Applies strict mathematical validation to observations.
        Filters out None, NaN, and Infinity.
        """
        valid = []
        for obs in observations:
            if obs.value is None:
                continue
            if not math.isfinite(obs.value):
                continue
            # Note: We do NOT filter <= 0 here because some metrics (e.g., temperatures or profitability) 
            # can be legitimately negative or zero. The domain-specific adapter is responsible for
            # stripping non-sensical values before passing them to the generic engine.
            valid.append(obs)
        return valid
