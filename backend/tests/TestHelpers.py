import time

from backend.helpers.job_manager_buffer import JobManagerBuffer
from backend.helpers.job_manager_sync import JobManagerSync
from backend.tests.TestJobManager import TestLocalJobManager
from common.courses import Course


class TestSync(TestLocalJobManager):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        return {"result": "success"}

    def test_sync(self):
        jbs = JobManagerSync(self.job_manager)
        result = jbs.new_job(Course('test').get_task('do_run'), {"problem_id": "0"})
        assert "result" in result and result["result"] == "success"


class TestBuffer(TestLocalJobManager):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        time.sleep(1)
        return {"result": "success"}

    def test_is_waiting(self):
        jbb = JobManagerBuffer(self.job_manager)
        jobid1 = jbb.new_job(Course('test').get_task('do_run'), {"problem_id": "0"})
        assert jbb.is_waiting(jobid1)
        time.sleep(2)
        assert jbb.get_result(jobid1)["result"] == "success"

    def test_is_done(self):
        jbb = JobManagerBuffer(self.job_manager)
        jobid1 = jbb.new_job(Course('test').get_task('do_run'), {"problem_id": "0"})
        time.sleep(2)
        assert jbb.is_done(jobid1)
        assert jbb.get_result(jobid1)["result"] == "success"
