import pytest
import math
from infrastructure.intelligence.core.financial import GenericFinancialImpactEngine, GenericFinancialImpactResult

@pytest.fixture
def generic_engine():
    return GenericFinancialImpactEngine()

def test_generic_financial_result_construction(generic_engine):
    payload = {
        "status": "SUCCESS",
        "entity_id": "T-100",
        "baseline_value": 15.0,
        "observed_value": 10.0,
        "estimated_financial_exposure": 1000.0,
        "currency": "INR",
        "domain_context": {"some_key": "some_value"}
    }
    
    result = generic_engine.validate_and_construct(payload)
    
    assert result.status == "SUCCESS"
    assert result.entity_id == "T-100"
    assert result.baseline_value == 15.0
    assert result.observed_value == 10.0
    assert result.estimated_financial_exposure == 1000.0
    assert result.domain_context == {"some_key": "some_value"}

def test_valid_exposure(generic_engine):
    payload = {
        "status": "SUCCESS",
        "estimated_financial_exposure": 150.5
    }
    result = generic_engine.validate_and_construct(payload)
    assert result.estimated_financial_exposure == 150.5

def test_zero_exposure(generic_engine):
    payload = {
        "status": "SUCCESS",
        "estimated_financial_exposure": 0.0
    }
    result = generic_engine.validate_and_construct(payload)
    assert result.estimated_financial_exposure == 0.0

def test_invalid_negative_exposure(generic_engine):
    payload = {
        "status": "SUCCESS",
        "estimated_financial_exposure": -500.0
    }
    result = generic_engine.validate_and_construct(payload)
    assert result.estimated_financial_exposure == 0.0

def test_nan_infinity_rejection(generic_engine):
    payload = {
        "status": "SUCCESS",
        "estimated_financial_exposure": float('inf')
    }
    result = generic_engine.validate_and_construct(payload)
    assert result.status == "INSUFFICIENT_DATA"
    assert result.reason == "NON_FINITE_FINANCIAL_EXPOSURE"
    
    payload = {
        "status": "SUCCESS",
        "estimated_financial_exposure": float('nan')
    }
    result = generic_engine.validate_and_construct(payload)
    assert result.status == "INSUFFICIENT_DATA"

def test_missing_domain_context_initialization(generic_engine):
    payload = {
        "status": "SUCCESS",
        "estimated_financial_exposure": 100.0
    }
    result = generic_engine.validate_and_construct(payload)
    assert result.domain_context == {}
