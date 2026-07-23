import unittest
from infrastructure.scheduler.executor import JobExecutor
from infrastructure.scheduler.registry import JobRegistry
from infrastructure.scheduler.tracking import JobTracker
from infrastructure.scheduler.repository import InMemoryExecutionRepository
from infrastructure.scheduler.models import Job, JobStatus

class TestJobExecutor(unittest.TestCase):
    def setUp(self):
        self.registry = JobRegistry()
        self.tracker = JobTracker(InMemoryExecutionRepository())
        self.executor = JobExecutor(self.registry, self.tracker)
        
    def test_successful_execution(self):
        payload_received = {}
        def handler(payload):
            payload_received.update(payload)
            
        self.registry.register("test_job", handler)
        job = Job(job_name="test", job_type="test_job", payload={"k": "v"})
        
        execution = self.executor.execute(job)
        self.assertEqual(execution.status, JobStatus.COMPLETED)
        self.assertEqual(payload_received, {"k": "v"})
        
    def test_failed_execution(self):
        def handler(payload):
            raise ValueError("Test error")
            
        self.registry.register("fail_job", handler)
        job = Job(job_name="fail", job_type="fail_job")
        
        execution = self.executor.execute(job)
        self.assertEqual(execution.status, JobStatus.FAILED)
        self.assertEqual(execution.error, "Test error")
