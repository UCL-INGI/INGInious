from backend.tests.TestJobManager import TestJobManager
from common.courses import Course

class TestNoAgent(TestJobManager):

    def test_no_agent(self):
        assert self.job_manager.number_agents_available() == 0

    def test_run_job(self):
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "crash"