import unittest
import uuid
from datetime import datetime, timezone, timedelta
from domain.driver.api import DriverAPI
from domain.driver.schemas import RegisterDriverRequest, StateChangeRequest
from domain.driver.models import EmploymentType, DriverStatus
from domain.driver.value_objects import DriverLicence, LicenceClass
from domain.driver.repository import InMemoryDriverRepository
from domain.driver.service import DriverService
from domain.driver.queries import DriverQueryService

class TestDriverPipeline(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryDriverRepository()
        self.service = DriverService(self.repo)
        self.queries = DriverQueryService(self.repo)
        self.api = DriverAPI(self.service, self.queries)
        
    def test_end_to_end_lifecycle(self):
        org_id = uuid.uuid4()
        
        # 1. Register
        req = RegisterDriverRequest(
            organization_id=org_id,
            employee_code="EMP-100",
            full_name="Jane Doe",
            phone_number="+19998887777",
            licence=DriverLicence(
                number="DL-555",
                licence_class=LicenceClass.COMMERCIAL,
                expiry_date=datetime.now(timezone.utc) + timedelta(days=365),
                state_of_issue="TX"
            ),
            employment_type=EmploymentType.CONTRACT
        )
        resp1 = self.api.register_driver(req)
        self.assertEqual(resp1.status, DriverStatus.INACTIVE)
        
        # 2. Activate
        resp2 = self.api.activate_driver(resp1.driver_id, StateChangeRequest(reason="Onboarding Complete"))
        self.assertEqual(resp2.status, DriverStatus.ACTIVE)
        
        # 3. Search
        active = self.api.list_organization_drivers(org_id)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].full_name, "Jane Doe")
        
        # 4. Suspend
        resp3 = self.api.suspend_driver(resp1.driver_id, StateChangeRequest(reason="Safety violation"))
        self.assertEqual(resp3.status, DriverStatus.SUSPENDED)
