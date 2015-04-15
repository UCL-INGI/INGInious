from backend.tests.TestFakeAgent import TestWithFakeAgent
from common.courses import Course

class TestAgentCrash(TestWithFakeAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        raise Exception("You shall not pass!")

    def default_callback(self, _, _2, result):
        self.got_result = result
        TestWithFakeAgent.default_callback(self, _, _2, result)

    def test_exception(self):
        self.got_result = None
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_1": "1"}, self.default_callback)
        self.wait_for_callback()
        assert "result" in self.got_result and self.got_result["result"] == "crash"