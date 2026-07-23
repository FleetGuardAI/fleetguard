import unittest
from pydantic import ValidationError
from infrastructure.intelligence.cross_domain.models import FleetInsight, InsightType, InsightStrength, FleetInsightCollection


class TestCrossDomainModels(unittest.TestCase):
    def test_fleet_insight_immutability(self):
        insight = FleetInsight(
            insight_key="cross.test",
            insight_type=InsightType.CORRELATION,
            insight_strength=InsightStrength.LOW,
            summary="test"
        )
        
        with self.assertRaises(ValidationError):
            insight.summary = "changed"
            
        with self.assertRaises(ValidationError):
            insight.new_field = "test"

    def test_fleet_insight_collection_immutability(self):
        col = FleetInsightCollection(insights=[])
        
        with self.assertRaises(ValidationError):
            col.execution_time = 1.0
