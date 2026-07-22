import unittest
from pydantic import ValidationError
from infrastructure.scheduler.models import Job, JobPriority

class TestSchedulerModels(unittest.TestCase):
    def test_job_immutability(self):
        job = Job(job_name="test", job_type="test_type")
        with self.assertRaises(ValidationError):
            job.priority = JobPriority.HIGH
