import unittest
from datetime import datetime, timezone, timedelta
from domain.driver.value_objects import EmployeeCode, DriverLicence, LicenceClass
from domain.driver.errors import InvalidIdentifier, InvalidLicence

class TestValueObjects(unittest.TestCase):
    def test_employee_code(self):
        valid = EmployeeCode(value="EMP-123")
        self.assertEqual(valid.value, "EMP-123")
        
        with self.assertRaises(InvalidIdentifier):
            EmployeeCode(value="")

    def test_licence(self):
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=365)
        past = now - timedelta(days=10)
        
        valid = DriverLicence(
            number="DL-12345",
            licence_class=LicenceClass.COMMERCIAL,
            expiry_date=future,
            state_of_issue="CA"
        )
        self.assertFalse(valid.is_expired())
        
        expired = DriverLicence(
            number="DL-999",
            licence_class=LicenceClass.COMMERCIAL,
            expiry_date=past,
            state_of_issue="NY"
        )
        self.assertTrue(expired.is_expired())
        
        with self.assertRaises(InvalidLicence):
            DriverLicence(
                number="",
                licence_class=LicenceClass.CLASS_A,
                expiry_date=future,
                state_of_issue="CA"
            )
