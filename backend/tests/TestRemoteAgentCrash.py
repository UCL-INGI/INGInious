from backend.tests.TestJobManager import TestWithFakeRemoteAgent
from common.courses import Course

class TestRemoteAgentCrash(TestWithFakeRemoteAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        raise Exception("You shall not pass!")

    def test_exception(self):
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "crash"