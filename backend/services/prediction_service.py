"""
FleetGuard — Predictive Intelligence & AI/ML Mathematical Engine
Services for calculating Breakdown Risk Index (BRI), Component Remaining Useful Life (RUL),
Fuel Theft & Anomaly Detection, Driver Safety Scoring (DRS), and Tyre Wear Degradation.
"""

import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# --- Schemas ---

class BreakdownRiskRequest(BaseModel):
    vehicle_id: str
    dtc_codes: List[str] = Field(default_factory=list, description="List of active OBD-II Diagnostic Trouble Codes")
    engine_temp_celsius: float = Field(default=85.0, description="Current engine coolant temperature")
    current_mileage_km: float = Field(default=120000.0, description="Current odometer reading")
    rated_overhaul_km: float = Field(default=500000.0, description="Manufacturer rated vehicle overhaul mileage")
    service_adherence_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Service adherence ratio 0.0-1.0")


class BreakdownRiskResponse(BaseModel):
    vehicle_id: str
    breakdown_risk_index: float = Field(..., description="Probability of failure (0.0 to 1.0 / 0% to 100%)")
    risk_tier: str = Field(..., description="LOW, MEDIUM, or HIGH")
    dtc_severity_score: float
    temperature_deviation_celsius: float
    mileage_ratio: float
    recommended_action: str


class RULRequest(BaseModel):
    part_type: str = Field(default="BRAKE_PADS", description="BRAKE_PADS, ENGINE_OIL, AIR_FILTER, TRANSMISSION_FLUID")
    accumulated_mileage_km: float
    payload_kg: float = Field(default=15000.0)
    max_capacity_kg: float = Field(default=25000.0)
    harsh_events_per_100km: float = Field(default=2.5)


class RULResponse(BaseModel):
    part_type: str
    rated_lifespan_km: float
    effective_lifespan_km: float
    accumulated_mileage_km: float
    remaining_useful_life_km: float
    survival_probability_pct: float
    maintenance_status: str


class FuelTheftEvaluationRequest(BaseModel):
    claimed_receipt_liters: float
    sensor_tank_before_liters: float
    sensor_tank_after_liters: float
    vehicle_speed_kmh: float = 0.0
    engine_status_on: bool = False
    static_drop_liters: float = 0.0


class FuelTheftEvaluationResponse(BaseModel):
    is_receipt_fraud_flagged: bool
    receipt_discrepancy_liters: float
    is_siphoning_flagged: bool
    static_siphon_drop_liters: float
    overall_fraud_risk: str
    explanation: str


class DriverSafetyRequest(BaseModel):
    driver_id: str
    total_distance_km: float = Field(..., gt=0.0)
    harsh_braking_count: int = 0
    harsh_acceleration_count: int = 0
    overspeeding_minutes: float = 0.0
    night_driving_distance_km: float = 0.0
    speed_variance_std: float = 5.0


class DriverSafetyResponse(BaseModel):
    driver_id: str
    driver_risk_score: float = Field(..., description="0 to 100 safety score (100 = perfect)")
    safety_rating_tier: str = Field(..., description="EXCELLENT, GOOD, MODERATE, HIGH_RISK")
    harsh_braking_rate_per_100km: float
    harsh_accel_rate_per_100km: float
    overspeeding_minutes_per_100km: float
    night_driving_percentage: float
    risk_factors: List[str]


class TyreWearRequest(BaseModel):
    initial_tread_mm: float = Field(default=18.0)
    current_distance_km: float = Field(default=45000.0)
    actual_pressure_psi: float = Field(default=100.0)
    rated_pressure_psi: float = Field(default=115.0)
    actual_load_kg: float = Field(default=18000.0)
    rated_load_kg: float = Field(default=20000.0)


class TyreWearResponse(BaseModel):
    estimated_current_tread_mm: float
    remaining_tread_mm: float
    wear_rate_mm_per_1000km: float
    remaining_distance_km: float
    tyre_health_status: str
    replacement_urgent: bool


# --- Service Core Implementation ---

DTC_SEVERITY_MAP = {
    # Critical Engine & Transmission DTCs (Weight = 4.0)
    "P0200": 4.0, "P0300": 4.0, "P0217": 4.0, "P0700": 4.0, "P0234": 4.0,
    # Major DTCs (Weight = 2.0)
    "P0101": 2.0, "P0420": 2.0, "P0128": 2.0, "P0500": 2.0,
    # Minor DTCs (Weight = 0.5)
    "P0113": 0.5, "P0440": 0.5, "P0455": 0.5
}


def calculate_breakdown_risk(req: BreakdownRiskRequest) -> BreakdownRiskResponse:
    """
    Computes Breakdown Risk Index (BRI) using logit sigmoid formula.
    """
    # 1. Calculate DTC Severity
    dtc_score = sum(DTC_SEVERITY_MAP.get(code.upper(), 1.0) for code in req.dtc_codes)
    
    # 2. Calculate Engine Temperature Deviation above 95°C normal baseline
    temp_dev = max(0.0, req.engine_temp_celsius - 95.0)

    # 3. Calculate Mileage Ratio with Weibull shape factor (alpha = 1.45)
    mileage_ratio = req.current_mileage_km / max(1.0, req.rated_overhaul_km)
    weibull_mileage = math.pow(mileage_ratio, 1.45)

    # 4. Maintenance Adherence Penalty
    maint_penalty = 1.0 - req.service_adherence_score

    # Logit calculation: z = -3.20 + 1.85*DTC + 0.045*TempDev + 1.20*Mileage^1.45 + -1.50*MaintScore
    beta_0 = -3.20
    beta_dtc = 1.85
    beta_temp = 0.045
    beta_mileage = 1.20
    beta_maint = -1.50

    z = beta_0 + (beta_dtc * dtc_score) + (beta_temp * temp_dev) + (beta_mileage * weibull_mileage) + (beta_maint * req.service_adherence_score)

    # Sigmoid function
    bri = 1.0 / (1.0 + math.exp(-z))
    bri_pct = round(bri * 100.0, 2)

    if bri_pct >= 70.0:
        tier = "HIGH"
        rec = "CRITICAL: Schedule immediate workshop inspection. High probability of roadside failure."
    elif bri_pct >= 30.0:
        tier = "MEDIUM"
        rec = "WARNING: Monitor vehicle telemetry closely. Schedule preventive service at next depot stop."
    else:
        tier = "LOW"
        rec = "NORMAL: Vehicle operating within safe mechanical parameters."

    return BreakdownRiskResponse(
        vehicle_id=req.vehicle_id,
        breakdown_risk_index=bri_pct,
        risk_tier=tier,
        dtc_severity_score=round(dtc_score, 2),
        temperature_deviation_celsius=round(temp_dev, 2),
        mileage_ratio=round(mileage_ratio, 3),
        recommended_action=rec
    )


def calculate_component_rul(req: RULRequest) -> RULResponse:
    """
    Computes Remaining Useful Life (RUL) using Weibull survival model.
    """
    baselines = {
        "BRAKE_PADS": 40000.0,
        "ENGINE_OIL": 15000.0,
        "AIR_FILTER": 25000.0,
        "TRANSMISSION_FLUID": 80000.0
    }
    eta_0 = baselines.get(req.part_type.upper(), 30000.0)
    beta = 2.1 # Weibull wear shape parameter

    # Stress factors
    payload_ratio = req.payload_kg / max(1.0, req.max_capacity_kg)
    gamma_load = 1.0 + 0.5 * payload_ratio
    gamma_driver = 0.8 + 0.4 * (req.harsh_events_per_100km / 2.0)
    gamma_temp = 1.05 # Baseline temp factor

    eta_effective = eta_0 / (gamma_load * gamma_driver * gamma_temp)

    # Survival Probability: R(t) = exp(- (M / eta)^beta)
    survival_prob = math.exp(- math.pow(req.accumulated_mileage_km / eta_effective, beta))

    # Remaining distance until survival prob drops to 10%
    target_survival = 0.10
    total_useful_km = eta_effective * math.pow(-math.log(target_survival), 1.0 / beta)
    rul_km = max(0.0, total_useful_km - req.accumulated_mileage_km)

    if rul_km <= 2000.0 or survival_prob <= 0.20:
        status = "REPLACEMENT_REQUIRED"
    elif rul_km <= 5000.0:
        status = "SERVICE_DUE_SOON"
    else:
        status = "HEALTHY"

    return RULResponse(
        part_type=req.part_type,
        rated_lifespan_km=eta_0,
        effective_lifespan_km=round(eta_effective, 1),
        accumulated_mileage_km=req.accumulated_mileage_km,
        remaining_useful_life_km=round(rul_km, 1),
        survival_probability_pct=round(survival_prob * 100.0, 1),
        maintenance_status=status
    )


def detect_fuel_theft_and_fraud(req: FuelTheftEvaluationRequest) -> FuelTheftEvaluationResponse:
    """
    Evaluates receipt discrepancy vs sensor data & static tank siphoning.
    """
    sensor_delta = req.sensor_tank_after_liters - req.sensor_tank_before_liters
    discrepancy = abs(req.claimed_receipt_liters - sensor_delta)

    # Threshold: Flag if discrepancy > 5 Liters OR > 5% of claimed volume
    allowed_tolerance = max(5.0, 0.05 * req.claimed_receipt_liters)
    is_receipt_fraud = discrepancy > allowed_tolerance

    # Siphoning check: Drop >= 3.5 Liters while parked
    is_siphon = req.static_drop_liters >= 3.5 and req.vehicle_speed_kmh == 0.0 and not req.engine_status_on

    if is_siphon and is_receipt_fraud:
        risk = "HIGH_CRITICAL"
        exp = f"CRITICAL: Both static tank siphoning ({req.static_drop_liters}L) and receipt over-billing discrepancy ({round(discrepancy, 1)}L) detected."
    elif is_siphon:
        risk = "HIGH_SIPHONING"
        exp = f"THEFT ALERT: Unexplained static fuel level drop of {req.static_drop_liters}L while vehicle was parked with engine OFF."
    elif is_receipt_fraud:
        risk = "MEDIUM_RECEIPT_FRAUD"
        exp = f"FRAUD ALERT: Claimed fuel receipt ({req.claimed_receipt_liters}L) exceeds actual tank sensor increase ({round(sensor_delta, 1)}L) by {round(discrepancy, 1)}L."
    else:
        risk = "CLEAN"
        exp = "VERIFIED: Fuel receipt volume aligns with IoT tank sensor delta within valid tolerance limits."

    return FuelTheftEvaluationResponse(
        is_receipt_fraud_flagged=is_receipt_fraud,
        receipt_discrepancy_liters=round(discrepancy, 2),
        is_siphoning_flagged=is_siphon,
        static_siphon_drop_liters=req.static_drop_liters,
        overall_fraud_risk=risk,
        explanation=exp
    )


def calculate_driver_safety_score(req: DriverSafetyRequest) -> DriverSafetyResponse:
    """
    Calculates 0-100 Driver Safety Score (DRS).
    """
    dist_100k = req.total_distance_km / 100.0

    hb_rate = req.harsh_braking_count / max(0.1, dist_100k)
    ha_rate = req.harsh_acceleration_count / max(0.1, dist_100k)
    os_rate = req.overspeeding_minutes / max(0.1, dist_100k)
    night_pct = (req.night_driving_distance_km / req.total_distance_km) * 100.0

    w_hb = 6.0
    w_ha = 4.0
    w_os = 3.5
    w_night = 0.15 # scaled from 15% max
    w_spd_var = 2.0

    deductions = (w_hb * hb_rate) + (w_ha * ha_rate) + (w_os * os_rate) + (w_night * night_pct) + (w_spd_var * req.speed_variance_std)

    drs = max(0.0, min(100.0, 100.0 - deductions))

    factors = []
    if hb_rate > 3.0:
        factors.append(f"High harsh braking frequency ({round(hb_rate, 1)} / 100km)")
    if ha_rate > 3.0:
        factors.append(f"Excessive rapid acceleration ({round(ha_rate, 1)} / 100km)")
    if os_rate > 5.0:
        factors.append(f"Extended overspeeding ({round(os_rate, 1)} mins / 100km)")
    if night_pct > 25.0:
        factors.append(f"Elevated night driving fatigue exposure ({round(night_pct, 1)}%)")

    if drs >= 85.0:
        tier = "EXCELLENT"
    elif drs >= 70.0:
        tier = "GOOD"
    elif drs >= 55.0:
        tier = "MODERATE"
    else:
        tier = "HIGH_RISK"

    return DriverSafetyResponse(
        driver_id=req.driver_id,
        driver_risk_score=round(drs, 1),
        safety_rating_tier=tier,
        harsh_braking_rate_per_100km=round(hb_rate, 2),
        harsh_accel_rate_per_100km=round(ha_rate, 2),
        overspeeding_minutes_per_100km=round(os_rate, 2),
        night_driving_percentage=round(night_pct, 1),
        risk_factors=factors
    )


def predict_tyre_wear(req: TyreWearRequest) -> TyreWearResponse:
    """
    Calculates tyre wear degradation and estimates remaining distance.
    """
    k0 = 0.12 # baseline wear: 0.12 mm per 1,000 km

    pressure_factor = math.pow(req.rated_pressure_psi / max(1.0, req.actual_pressure_psi), 1.6)
    load_factor = math.pow(req.actual_load_kg / max(1.0, req.rated_load_kg), 1.3)

    k_wear = k0 * pressure_factor * load_factor

    distance_thousands = req.current_distance_km / 1000.0
    wear_accumulated = k_wear * distance_thousands

    current_tread = max(0.0, req.initial_tread_mm - wear_accumulated)
    min_legal_tread = 1.6
    remaining_usable_tread = max(0.0, current_tread - min_legal_tread)

    remaining_distance_km = (remaining_usable_tread / k_wear) * 1000.0

    if current_tread <= 3.0:
        status = "CRITICAL_WEAR"
        urgent = True
    elif current_tread <= 6.0:
        status = "INSPECT_SOON"
        urgent = False
    else:
        status = "GOOD_CONDITION"
        urgent = False

    return TyreWearResponse(
        estimated_current_tread_mm=round(current_tread, 2),
        remaining_tread_mm=round(remaining_usable_tread, 2),
        wear_rate_mm_per_1000km=round(k_wear, 4),
        remaining_distance_km=round(remaining_distance_km, 0),
        tyre_health_status=status,
        replacement_urgent=urgent
    )
