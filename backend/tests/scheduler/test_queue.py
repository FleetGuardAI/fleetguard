import unittest
from infrastructure.scheduler.queue import InMemoryJobQueue
from infrastructure.scheduler.models import Job

class TestJobQueue(unittest.TestCase):
    def test_enqueue_dequeue(self):
        queue = InMemoryJobQueue()
        job = Job(job_name="test", job_type="test")
        
        queue.enqueue(job)
        self.assertEqual(queue.get_size(), 1)
        
        popped = queue.dequeue()
        self.assertEqual(popped.job_id, job.job_id)
        self.assertEqual(queue.get_size(), 0)
        
        self.assertIsNone(queue.dequeue())
