from backend.tests.TestJobManager import TestWithFakeRemoteAgent
from common.courses import Course
import time

class TestRemoteAgentOK(TestWithFakeRemoteAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        return {"result": "success", "grade": 100.0}

    def get_task_directory_hashes_func(self):
        return {"todelete": ("a random invalid hash", 3456)}

    def update_task_directory_func(self, remote_tar_file, to_delete):
        self.remote_tar_file = remote_tar_file
        self.nb_calls = self.nb_calls+1
        if self.nb_calls == 1:
            self.to_delete1 = to_delete
        elif self.nb_calls == 2:
            self.to_delete2 = to_delete

    def test_job(self):
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"

    def test_update_task_directory(self):
        self.nb_calls = 0
        self.to_delete1 = []
        self.to_delete2 = []
        self.job_manager._last_content_in_task_directory = {}
        time.sleep(5)  # give a little time to allow everything to connect, compressing the files, ...
        assert self.nb_calls == 2
        assert self.to_delete1 == ["todelete"]
        assert self.to_delete2 == ["todelete"]
        assert len(self.remote_tar_file) > 300

class TestRemoteAgentNoSync(TestWithFakeRemoteAgent):
    error = False

    def get_task_directory_hashes_func(self):
        return None

    def update_task_directory_func(self, remote_tar_file, to_delete):
        self.error = True
        assert False

    def test_nosync(self):
        # give a little time to allow everything to connect...
        time.sleep(2)
        assert not self.error
        # If this, runs, it's ok!
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"