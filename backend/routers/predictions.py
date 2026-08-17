"""
FleetGuard — Predictions & AI/ML Router
API endpoints for executing real-time breakdown risk, RUL, fuel fraud, driver safety, and tyre wear calculations.
"""

from fastapi import APIRouter
from services.prediction_service import (
    BreakdownRiskRequest, BreakdownRiskResponse, calculate_breakdown_risk,
    RULRequest, RULResponse, calculate_component_rul,
    FuelTheftEvaluationRequest, FuelTheftEvaluationResponse, detect_fuel_theft_and_fraud,
    DriverSafetyRequest, DriverSafetyResponse, calculate_driver_safety_score,
    TyreWearRequest, TyreWearResponse, predict_tyre_wear
)

router = APIRouter(prefix="/predictions", tags=["Predictive Analytics & AI Engine"])


@router.post("/breakdown-risk", response_model=BreakdownRiskResponse)
async def evaluate_breakdown_risk(req: BreakdownRiskRequest) -> BreakdownRiskResponse:
    """
    Calculate Vehicle Breakdown Risk Index (BRI) using logit sigmoid & Weibull wear factors.
    """
    return calculate_breakdown_risk(req)


@router.post("/remaining-useful-life", response_model=RULResponse)
async def evaluate_component_rul(req: RULRequest) -> RULResponse:
    """
    Estimate Remaining Useful Life (RUL) for vehicle components using survival models.
    """
    return calculate_component_rul(req)


@router.post("/fuel-theft-check", response_model=FuelTheftEvaluationResponse)
async def evaluate_fuel_theft(req: FuelTheftEvaluationRequest) -> FuelTheftEvaluationResponse:
    """
    Detect fuel receipt fraud (OCR vs tank sensor) and static tank siphoning.
    """
    return detect_fuel_theft_and_fraud(req)


@router.post("/driver-safety-score", response_model=DriverSafetyResponse)
async def evaluate_driver_safety(req: DriverSafetyRequest) -> DriverSafetyResponse:
    """
    Calculate 0-100 Driver Risk Score (DRS) based on harsh events, overspeeding, and night driving.
    """
    return calculate_driver_safety_score(req)


@router.post("/tyre-wear", response_model=TyreWearResponse)
async def evaluate_tyre_wear(req: TyreWearRequest) -> TyreWearResponse:
    """
    Predict tyre tread degradation and remaining distance based on pressure and load.
    """
    return predict_tyre_wear(req)
