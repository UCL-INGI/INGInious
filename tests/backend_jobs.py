import unittest
import common.base
import common.tasks
import common.courses
import frontend
import frontend.submission_manager
import uuid
import time
from tests import *

class backend_jobs(unittest.TestCase):
    def setUp(self):
        print "\033[1m-> backend_jobs:setUp\033[0m"
    
    def job_finished(self, jid, final_dict):
        assert self.jid == jid
        assert final_dict['result'] == "success"
    
    def test_job_adding(self):
        t = common.tasks.Task(common.courses.Course('test'), 'task1')
        self.jid = queue.add_job(t, {"input":{"unittest/decimal":"12.5"}, "limits":t.get_limits()}, self.job_finished)
        assert isinstance(self.jid, uuid.UUID)
        
        while not queue.is_done(self.jid):
            time.sleep(1)
        
    def tearDown(self):
        print "\033[1m-> backend_jobs:tearDown\033[0m"

if __name__ == "__main__":
    queue = frontend.submission_manager.get_backend_job_queue.job_queue
    unittest.main()
