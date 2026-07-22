import unittest
from datetime import datetime, timezone, timedelta
from infrastructure.scheduler.scheduler import Scheduler
from infrastructure.scheduler.repository import InMemoryJobRepository, InMemoryExecutionRepository
from infrastructure.scheduler.queue import InMemoryJobQueue
from infrastructure.scheduler.executor import JobExecutor
from infrastructure.scheduler.registry import JobRegistry
from infrastructure.scheduler.tracking import JobTracker
from infrastructure.scheduler.worker import JobWorker
from infrastructure.scheduler.models import Job, ScheduleType, JobStatus

class TestSchedulerPipeline(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryJobRepository()
        self.queue = InMemoryJobQueue()
        self.scheduler = Scheduler(self.repo, self.queue)
        
        self.registry = JobRegistry()
        self.tracker = JobTracker(InMemoryExecutionRepository())
        self.executor = JobExecutor(self.registry, self.tracker)
        
        self.worker = JobWorker(self.queue, self.executor)
        
    def test_end_to_end_pipeline(self):
        # 1. Register handler
        results = []
        def handler(payload):
            results.append(payload["msg"])
            
        self.registry.register("print_job", handler)
        
        # 2. Schedule job
        job = Job(job_name="test1", job_type="print_job", payload={"msg": "hello"}, schedule_type=ScheduleType.ONCE)
        self.scheduler.schedule(job)
        
        # 3. Job is immediately queued
        self.assertEqual(self.queue.get_size(), 1)
        
        # 4. Worker processes it
        processed = self.worker.process_next()
        self.assertTrue(processed)
        self.assertEqual(self.queue.get_size(), 0)
        
        # 5. Handler executed
        self.assertEqual(results, ["hello"])
        
        # 6. Tracking updated
        history = self.tracker.get_history(job.job_id)
        self.assertEqual(len(history), 2)  # RUNNING, COMPLETED
        self.assertEqual(history[-1].status, JobStatus.COMPLETED)
