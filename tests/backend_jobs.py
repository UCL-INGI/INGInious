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
        self.queue = frontend.submission_manager.get_backend_job_queue.job_queue
    
    def job_finished(self, jid, final_dict):
        '''Catches ending of a test job and tests the final state of the queue'''
        self.done = True
        # Check if received job matches and if state in the queue is not running
        assert self.jid == jid
        assert not self.queue.is_running(jid)
        
        # Check removal procedure
        assert self.queue.is_done(jid)
        self.queue.get_result(jid)
        assert not self.queue.is_done(jid)
        
        # Check content of the result
        assert final_dict['result'] == "success"
        
        # Check if result is no more available in queue
        assert self.queue.get_result(jid) == None
    
    def test_queue_job_processing(self):
        '''Tests if a job adds in the queue and is treated correctly'''
        print "\033[1m-> backend-jobs: queue job processing \033[0m"
        self.done = False
        t = common.tasks.Task(common.courses.Course('test'), 'task1')
        self.jid = self.queue.add_job(t, {"input":{"unittest/decimal":"12.5"}, "limits":t.get_limits()}, self.job_finished)
        assert isinstance(self.jid, uuid.UUID)
        
        while not self.done:
            time.sleep(1)
            print "Waiting for the job to end..."
        
        print "Job finished"
    
    def test_docker_job(self):
        '''Tests if a job runs correctly in Docker'''
        print "\033[1m-> backend-jobs: docker job processing \033[0m"
        djm = DockerJobManager(self.queue, INGIniousConfiguration["docker_server_url"], INGIniousConfiguration["tasks_directory"], INGIniousConfiguration["containers_directory"], INGIniousConfiguration["container_prefix"])
        t = common.tasks.Task(common.courses.Course('test'), 'task1')
        test_result = djm.run_job(0, t, {"input":{"unittest/decimal":"12.5"}, "limits":t.get_limits()})
        assert test_result['result'] == 'success'
        
        
    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()
