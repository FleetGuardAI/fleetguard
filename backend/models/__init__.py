"""
FleetGuard ORM Models Package.
Import all models here so Base.metadata picks them up for table creation.
"""

from models.truck import Truck
from models.driver import Driver
from models.ticket import Ticket
from models.fuel_log import FuelLog

__all__ = ["Truck", "Driver", "Ticket", "FuelLog"]
