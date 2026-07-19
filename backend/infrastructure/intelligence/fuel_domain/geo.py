import abc
import math

class DistanceCalculator(abc.ABC):
    """
    Abstract interface for geographic distance calculations.
    """
    @abc.abstractmethod
    def calculate_distance_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        pass


class HaversineDistanceCalculator(DistanceCalculator):
    """
    Computes distance between two coordinates using the Haversine formula.
    """
    def calculate_distance_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000.0  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2.0) ** 2
            
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
