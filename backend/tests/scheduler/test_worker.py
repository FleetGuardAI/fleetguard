import unittest
from unittest.mock import MagicMock
from infrastructure.scheduler.worker import JobWorker
from infrastructure.scheduler.queue import InMemoryJobQueue
from infrastructure.scheduler.models import Job

class TestJobWorker(unittest.TestCase):
    def test_worker_processing(self):
        queue = InMemoryJobQueue()
        executor_mock = MagicMock()
        worker = JobWorker(queue, executor_mock)
        
        job = Job(job_name="test", job_type="test")
        queue.enqueue(job)
        
        processed = worker.process_next()
        self.assertTrue(processed)
        executor_mock.execute.assert_called_once_with(job)
        
        # Queue should be empty now
        processed_again = worker.process_next()
        self.assertFalse(processed_again)
