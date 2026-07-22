"""
Driver Management Domain - Schemas
"""

import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from domain.driver.models import EmploymentType
from domain.driver.value_objects import DriverLicence

class RegisterDriverRequest(BaseModel):
    organization_id: uuid.UUID
    employee_code: str
    full_name: str
    phone_number: str
    licence: DriverLicence
    employment_type: EmploymentType
    email: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class StateChangeRequest(BaseModel):
    reason: Optional[str] = None
