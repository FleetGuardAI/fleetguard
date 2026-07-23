import unittest
import uuid
from datetime import datetime, timezone, timedelta
from domain.driver.schemas import RegisterDriverRequest
from domain.driver.models import EmploymentType
from domain.driver.value_objects import DriverLicence, LicenceClass
from domain.driver.repository import InMemoryDriverRepository
from domain.driver.service import DriverService
from domain.driver.errors import DuplicateDriver, DuplicateLicence

class TestDriverService(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryDriverRepository()
        self.service = DriverService(self.repo)
        self.org_id = uuid.uuid4()
        self.licence = DriverLicence(
            number="DL-1",
            licence_class=LicenceClass.CLASS_A,
            expiry_date=datetime.now(timezone.utc) + timedelta(days=100),
            state_of_issue="CA"
        )
        
    def test_register_duplicate_employee_code(self):
        req = RegisterDriverRequest(
            organization_id=self.org_id,
            employee_code="DUP-1",
            full_name="John Doe",
            phone_number="+1234567890",
            licence=self.licence,
            employment_type=EmploymentType.FULL_TIME
        )
        self.service.register_driver(req)
        
        req2 = req.model_copy(update={"licence": DriverLicence(number="DL-2", licence_class=LicenceClass.CLASS_A, expiry_date=self.licence.expiry_date, state_of_issue="CA")})
        with self.assertRaises(DuplicateDriver):
            self.service.register_driver(req2)
            
    def test_register_duplicate_licence(self):
        req = RegisterDriverRequest(
            organization_id=self.org_id,
            employee_code="E-1",
            full_name="John Doe",
            phone_number="+1234567890",
            licence=self.licence,
            employment_type=EmploymentType.FULL_TIME
        )
        self.service.register_driver(req)
        
        req2 = req.model_copy(update={"employee_code": "E-2"})
        with self.assertRaises(DuplicateLicence):
            self.service.register_driver(req2)
