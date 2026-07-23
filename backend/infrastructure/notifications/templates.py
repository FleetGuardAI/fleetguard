"""
Notification Service - Templates
"""

from typing import Dict, Any

class NotificationTemplates:
    """
    Registry for simple string interpolation templates.
    No conditional business logic is permitted here.
    """
    
    _TEMPLATES = {
        "fuel_theft_alert": "ALERT: Suspected fuel theft of {amount}L detected on vehicle {vehicle_id} at {location}.",
        "maintenance_reminder": "REMINDER: Vehicle {vehicle_id} is due for maintenance on {due_date}.",
        "insurance_expiry": "WARNING: Insurance for {vehicle_id} expires on {expiry_date}.",
        "driver_licence_expiry": "WARNING: Licence for driver {driver_name} expires on {expiry_date}.",
        "fleet_summary": "SUMMARY: Fleet '{fleet_name}' operated {total_distance}km today."
    }

    @classmethod
    def render(cls, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renders a template using standard string substitution.
        Raises KeyError if the template doesn't exist or if required context keys are missing.
        """
        if template_name not in cls._TEMPLATES:
            raise KeyError(f"Template '{template_name}' not found.")
            
        template_str = cls._TEMPLATES[template_name]
        try:
            return template_str.format(**context)
        except KeyError as e:
            raise KeyError(f"Missing required context variable for template '{template_name}': {str(e)}")
