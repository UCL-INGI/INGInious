import unittest
from common.base import INGIniousConfiguration
import common.base
import common.tasks
import common.courses
from backend.job_manager import JobManager
from backend.docker_job_manager import DockerJobManager
import frontend
import frontend.submission_manager
import uuid
import time
from tests import *

class backend_jobs(unittest.TestCase):
    def setUp(self):
        print "\033[1m-> backend_jobs:setUp\033[0m"
    
    def job_finished(self, jid, final_dict):
        '''Catch ending of a test job and tests the final state of the queue'''
        self.done = True
        # Check if received job matches and if state in the queue is not running
        assert self.jid == jid
        assert not queue.is_running(jid)
        
        # Check removal procedure
        assert queue.is_done(jid)
        queue.get_result(jid)
        assert not queue.is_done(jid)
        
        # Check content of the result
        assert final_dict['result'] == "success"
        
        # Check if result is no more available in queue
        assert queue.get_result(jid) == None
    
    def test_job_queue_processing(self):
        '''Tests if a job adds in the queue and is treated correctly'''
        self.done = False
        t = common.tasks.Task(common.courses.Course('test'), 'task1')
        self.jid = queue.add_job(t, {"input":{"unittest/decimal":"12.5"}, "limits":t.get_limits()}, self.job_finished)
        assert isinstance(self.jid, uuid.UUID)
        
        while not self.done:
            time.sleep(1)
            print "Waiting for the job to end..."
        
        print "Job finished"
    
    def test_docker_job(self):
        '''Tests if a job runs correctly in Docker'''
        djm = DockerJobManager(queue, INGIniousConfiguration["docker_server_url"], INGIniousConfiguration["tasks_directory"], INGIniousConfiguration["containers_directory"], INGIniousConfiguration["container_prefix"])
        t = common.tasks.Task(common.courses.Course('test'), 'task1')
        test_result = djm.run_job(0, t, {"input":{"unittest/decimal":"12.5"}, "limits":t.get_limits()})
        assert test_result['result'] == 'success'
        
        
    def tearDown(self):
        print "\033[1m-> backend_jobs:tearDown\033[0m"

if __name__ == "__main__":
    queue = frontend.submission_manager.get_backend_job_queue.job_queue
    unittest.main()
