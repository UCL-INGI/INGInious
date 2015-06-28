""" Theses tests checks that the backend is bad-agent-proof """
import time

from backend.tests.TestJobManager import TestWithFakeRemoteAgent
from common.courses import Course


class TestRemoteAgentJobCrash(TestWithFakeRemoteAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        raise Exception("You shall not pass!")

    def test_exception_job(self):
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "crash"


class TestRemoteAgentAliasUpdateCrash(TestWithFakeRemoteAgent):
    def update_image_aliases_func(self, image_aliases):
        raise Exception("Pass, you shall not.")

    def test_exception_alias(self):
        time.sleep(2)  # allow the exception to propagate through the different thread linked via RPyC
        # If this, runs, it's ok!
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"


class TestRemoteAgentTaskUpdateCrash1(TestWithFakeRemoteAgent):
    def get_task_directory_hashes_func(self):
        raise Exception(".")

    def test_exception_task_1(self):
        time.sleep(2)  # allow the exception to propagate through the different thread linked via RPyC
        # If this, runs, it's ok!
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"


class TestRemoteAgentTaskUpdateCrash2(TestWithFakeRemoteAgent):
    def update_task_directory_func(self, remote_tar_file, to_delete):
        raise Exception(".")

    def test_exception_task_2(self):
        time.sleep(5)  # allow the exception to propagate through the different thread linked via RPyC
        # If this, runs, it's ok!
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"
