import unittest
import uuid
from datetime import datetime, timezone, timedelta
from domain.driver.models import Driver, EmploymentType, DriverStatus
from domain.driver.value_objects import EmployeeCode, PhoneNumber, DriverLicence, LicenceClass
from domain.driver.aggregate import DriverAggregate
from domain.driver.errors import InvalidDriverState
from domain.driver.events import DriverRegistered

class TestDriverAggregate(unittest.TestCase):
    def setUp(self):
        self.driver = Driver(
            organization_id=uuid.uuid4(),
            employee_code=EmployeeCode(value="E1"),
            full_name="John Doe",
            phone_number=PhoneNumber(value="+1234567890"),
            licence=DriverLicence(
                number="DL-1",
                licence_class=LicenceClass.CLASS_A,
                expiry_date=datetime.now(timezone.utc) + timedelta(days=100),
                state_of_issue="CA"
            ),
            employment_type=EmploymentType.FULL_TIME
        )
        
    def test_register_driver(self):
        registered, events = DriverAggregate.register_driver(self.driver)
        self.assertEqual(registered.status, DriverStatus.INACTIVE)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], DriverRegistered)
        
    def test_suspend_driver(self):
        suspended, events = DriverAggregate.suspend_driver(self.driver)
        self.assertEqual(suspended.status, DriverStatus.SUSPENDED)
        
    def test_archive_driver(self):
        archived, events = DriverAggregate.archive_driver(self.driver)
        self.assertEqual(archived.status, DriverStatus.ARCHIVED)
        
        with self.assertRaises(InvalidDriverState):
            DriverAggregate.activate_driver(archived)
