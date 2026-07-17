from typing import Optional
from pydantic import BaseModel


class TruckBase(BaseModel):
    license_plate: str
    make: str
    model: Optional[str] = None
    year: Optional[int] = None
    tank_capacity: float = 400.0
    is_active: bool = True


class TruckCreate(TruckBase):
    pass


class TruckUpdate(BaseModel):
    license_plate: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    tank_capacity: Optional[float] = None
    is_active: Optional[bool] = None


class TruckResponse(TruckBase):
    id: int
    company_id: int

    model_config = {
        "from_attributes": True
    }