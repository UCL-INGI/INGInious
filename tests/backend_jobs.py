import unittest
from common.base import INGIniousConfiguration
import common.base
import common.tasks
import common.courses
from backend.job_manager import JobManager
import frontend
import frontend.submission_manager
import uuid
import time
from tests import *

class backend_jobs(unittest.TestCase):
    def setUp(self):
        self.jm = frontend.submission_manager.get_job_manager.job_manager
    
    def job_finished(self, jid, task, final_dict):
        '''Catches ending of a test job and tests the final state of the queue'''
        self.done = True
        
        # Check if received job matches and if state in the queue is not running
        assert self.jid == jid
        
        # Check content of the result
        assert final_dict['result'] == "success"
    
    def test_job_manager(self):
        '''Tests if a job adds in the queue and is treated correctly'''
        print "\033[1m-> backend-jobs: job manager\033[0m"
        self.done = False
        t = common.tasks.Task(common.courses.Course('test'), 'task1')
        self.jid = self.jm.new_job(t, {"input":{"unittest/decimal":"12.5"}, "limits":t.get_limits()}, self.job_finished)
        assert isinstance(self.jid, uuid.UUID)
        
        while not self.done:
            time.sleep(1)
            print "Waiting for the job to end..."
        
        print "Job finished"
    
    def test_submitter(self):
        '''Tests submission to docker'''
        print "\033[1m-> backend-jobs: submitter\033[0m"
        
    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()
