"""
FleetGuard — Cost Estimation Service
Calculates fuel consumption, fuel costs, toll costs, and total direct travel expenses.
"""

from typing import Optional, Tuple
from services.routing.schemas import CostEstimate


# Default benchmark values for commercial transport in India
DEFAULT_DIESEL_PRICE_INR = 90.0

DEFAULT_MILEAGE_BY_CLASS = {
    "LIGHT_COMMERCIAL": 8.0,
    "MEDIUM_DUTY": 5.5,
    "HEAVY_DUTY": 3.8,
    "TRAILER": 3.0,
    "TANKER": 3.2,
}
DEFAULT_FLEET_MILEAGE = 4.0  # Commercial truck default


class CostCalculationService:
    """
    Dedicated, deterministic cost estimation service.
    Direct travel cost = Fuel cost + Toll charges.
    """

    @staticmethod
    def calculate_cost(
        distance_km: float,
        vehicle_mileage: Optional[float] = None,
        fuel_price: Optional[float] = None,
        toll_estimate: Optional[float] = None,
        tolls_available: bool = True,
        vehicle_class: Optional[str] = None,
        currency: str = "INR"
    ) -> CostEstimate:
        disclosures = []

        # 1. Resolve Mileage
        effective_mileage = vehicle_mileage
        if effective_mileage is None or effective_mileage <= 0:
            if vehicle_class and vehicle_class.upper() in DEFAULT_MILEAGE_BY_CLASS:
                effective_mileage = DEFAULT_MILEAGE_BY_CLASS[vehicle_class.upper()]
                disclosures.append(f"Mileage based on {vehicle_class} standard ({effective_mileage:.1f} km/L).")
            else:
                effective_mileage = DEFAULT_FLEET_MILEAGE
                disclosures.append(f"Default fleet mileage assumed ({effective_mileage:.1f} km/L).")

        # 2. Resolve Fuel Price
        effective_price = fuel_price
        if effective_price is None or effective_price <= 0:
            effective_price = DEFAULT_DIESEL_PRICE_INR
            disclosures.append(f"Standard diesel benchmark used (₹{effective_price:.2f}/L).")

        # 3. Calculate Fuel Consumption and Cost
        fuel_liters = round(distance_km / effective_mileage, 2)
        fuel_cost = round(fuel_liters * effective_price, 2)

        # 4. Toll Charges
        final_toll = None
        if tolls_available and toll_estimate is not None:
            final_toll = round(toll_estimate, 2)
        else:
            final_toll = None
            disclosures.append("Toll estimates unavailable from routing provider.")

        # 5. Direct Travel Cost (fuel + tolls if available)
        direct_travel_cost = fuel_cost
        if final_toll is not None:
            direct_travel_cost += final_toll
        direct_travel_cost = round(direct_travel_cost, 2)

        return CostEstimate(
            distance_km=round(distance_km, 2),
            fuel_liters=fuel_liters,
            fuel_cost=fuel_cost,
            fuel_price_per_liter=effective_price,
            vehicle_mileage_km_per_liter=effective_mileage,
            toll_estimate=final_toll,
            tolls_available=(final_toll is not None),
            direct_travel_cost=direct_travel_cost,
            currency=currency,
            disclosures=disclosures
        )
