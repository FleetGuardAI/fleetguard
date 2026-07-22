import unittest
from datetime import datetime, timezone, timedelta
from infrastructure.scheduler.scheduler import Scheduler
from infrastructure.scheduler.repository import InMemoryJobRepository
from infrastructure.scheduler.queue import InMemoryJobQueue
from infrastructure.scheduler.models import Job, ScheduleType, RecurrencePolicy

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryJobRepository()
        self.queue = InMemoryJobQueue()
        self.scheduler = Scheduler(self.repo, self.queue)
        
    def test_schedule_immediate(self):
        job = Job(job_name="immediate", job_type="test", schedule_type=ScheduleType.ONCE)
        self.scheduler.schedule(job)
        
        self.assertEqual(self.queue.get_size(), 1)
        self.assertIsNotNone(self.repo.get(job.job_id))
        
    def test_schedule_delayed(self):
        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        job = Job(job_name="delayed", job_type="test", schedule_type=ScheduleType.DELAYED, scheduled_at=future_time)
        self.scheduler.schedule(job)
        
        # Should not be queued yet
        self.assertEqual(self.queue.get_size(), 0)
        self.assertIsNotNone(self.repo.get(job.job_id))
        
    def test_enqueue_due_jobs(self):
        now = datetime.now(timezone.utc)
        past_time = now - timedelta(minutes=5)
        future_time = now + timedelta(minutes=5)
        
        # Manipulate repo directly to bypass validation for test
        due_job = Job(job_name="due", job_type="test", schedule_type=ScheduleType.DELAYED, scheduled_at=past_time)
        not_due_job = Job(job_name="not_due", job_type="test", schedule_type=ScheduleType.DELAYED, scheduled_at=future_time)
        
        self.repo.save(due_job)
        self.repo.save(not_due_job)
        
        enqueued = self.scheduler.enqueue_due_jobs()
        self.assertEqual(enqueued, 1)
        self.assertEqual(self.queue.get_size(), 1)
        
        # The due job should be deleted from repo since it was a DELAYED one-time execution
        self.assertIsNone(self.repo.get(due_job.job_id))
        self.assertIsNotNone(self.repo.get(not_due_job.job_id))

    def test_enqueue_due_recurring_jobs(self):
        now = datetime.now(timezone.utc)
        past_time = now - timedelta(minutes=5)
        
        recurring_job = Job(
            job_name="recurring", 
            job_type="test", 
            schedule_type=ScheduleType.RECURRING, 
            scheduled_at=past_time,
            recurrence_policy=RecurrencePolicy(interval_seconds=3600)
        )
        
        self.repo.save(recurring_job)
        enqueued = self.scheduler.enqueue_due_jobs()
        self.assertEqual(enqueued, 1)
        
        # Recurring job should remain in repo with updated scheduled_at
        updated_job = self.repo.get(recurring_job.job_id)
        self.assertIsNotNone(updated_job)
        self.assertGreater(updated_job.scheduled_at, now)
