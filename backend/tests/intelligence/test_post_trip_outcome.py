import pytest
from services.trip_intelligence_service import TripIntelligenceService
from models.trip_domain import Trip

def test_outperformed_outcome():
    trip = Trip(
        intelligence_snapshot={
            "expected_profit": 10000
        }
    )
    # Net profit > 10% more than expected profit
    net_profit = 12000
    outcome = TripIntelligenceService._compute_recommendation_outcome(trip, net_profit)
    assert outcome == "OUTPERFORMED"

def test_met_expectation_outcome():
    trip = Trip(
        intelligence_snapshot={
            "expected_profit": 10000
        }
    )
    # Net profit within 10% of expected
    net_profit = 9500
    outcome = TripIntelligenceService._compute_recommendation_outcome(trip, net_profit)
    assert outcome == "MET_EXPECTATION"

def test_underperformed_outcome():
    trip = Trip(
        intelligence_snapshot={
            "expected_profit": 10000
        }
    )
    # Net profit < 10% below expected, but still > 0
    net_profit = 8000
    outcome = TripIntelligenceService._compute_recommendation_outcome(trip, net_profit)
    assert outcome == "UNDERPERFORMED"

def test_loss_outcome():
    trip = Trip(
        intelligence_snapshot={
            "expected_profit": 10000
        }
    )
    # Net profit <= 0
    net_profit = -500
    outcome = TripIntelligenceService._compute_recommendation_outcome(trip, net_profit)
    assert outcome == "LOSS"

def test_no_snapshot():
    trip = Trip(intelligence_snapshot=None)
    net_profit = 10000
    outcome = TripIntelligenceService._compute_recommendation_outcome(trip, net_profit)
    assert outcome is None
