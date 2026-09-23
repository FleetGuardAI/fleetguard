from typing import Optional
from infrastructure.validation.rule import BaseValidationRule
from schemas.validation_sdk import ValidationContext, RuleResult, RuleStatus, RuleSeverity, RuleCategory
from models.operational_event import EventType
from services.location_provider import LocationProvider

class ExpenseLocationFraudRule(BaseValidationRule):
    """
    Geographic Expense Fraud Detection:
    Cross-references the city extracted from the receipt (via OCR) with the 
    actual GPS coordinates of the truck at the time the receipt was logged.
    Requires Google Maps Reverse Geocoding.
    """

    @property
    def name(self) -> str:
        return "expense_geographic_fraud_rule"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.FRAUD

    @property
    def priority(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return "Verifies that the vehicle was in the same city as the receipt location at the time of the expense."

    def applies_to(self, context: ValidationContext) -> bool:
        if context.event.event_type != EventType.EXPENSE_ADDED:
            return False
            
        payload = context.event.payload or {}
        ocr_location = payload.get("ocr_location")
        
        # In a real scenario, business_state would contain the vehicle's last_location
        # For simplicity, we check if it's there
        return bool(ocr_location)

    async def evaluate(self, context: ValidationContext) -> RuleResult:
        payload = context.event.payload
        ocr_location = str(payload.get("ocr_location")).lower().strip()
        
        # Assuming vehicle state is populated in context.business_state["vehicle"] by the Orchestrator
        vehicle_data = context.business_state.get("vehicle", {})
        last_lat = vehicle_data.get("last_location_lat")
        last_lng = vehicle_data.get("last_location_lng")
        
        if not last_lat or not last_lng:
            return RuleResult(
                rule_name=self.name,
                status=RuleStatus.SKIPPED,
                message="Vehicle location data not available in business state."
            )

        # Call Google Maps Reverse Geocoding API
        location_provider = LocationProvider()
        actual_city = await location_provider.reverse_geocode(
            lat=last_lat, 
            lng=last_lng
        )
        
        if not actual_city:
            return RuleResult(
                rule_name=self.name,
                status=RuleStatus.SKIPPED,
                message="Reverse geocoding failed."
            )

        if ocr_location in actual_city or actual_city in ocr_location:
            return RuleResult(
                rule_name=self.name,
                status=RuleStatus.PASS,
                message=f"Location verified: Vehicle was in {actual_city}",
                metadata={"ocr_location": ocr_location, "actual_city": actual_city}
            )
        else:
            return RuleResult(
                rule_name=self.name,
                status=RuleStatus.FAIL,
                severity=RuleSeverity.CRITICAL,
                message=f"GEOGRAPHIC FRAUD DETECTED: Receipt from '{ocr_location}', but vehicle was in '{actual_city}'",
                metadata={"ocr_location": ocr_location, "actual_city": actual_city}
            )
