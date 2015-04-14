from backend.tests.TestFakeAgent import TestWithFakeAgent
from common.courses import Course

class TestNotInAgent(TestWithFakeAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        self.was_in = True
        return {"result": "success"}

    def test_ok(self):
        self.was_in = False
        self.job_manager.new_job(Course('test').get_task('no_run'), {"problem_id": "1"}, self.default_callback)
        self.wait_for_callback()
        assert not self.was_in

    def test_fail(self):
        self.was_in = False
        self.job_manager.new_job(Course('test').get_task('do_run'), {"problem_id": "1"}, self.default_callback)
        self.wait_for_callback()
        assert self.was_in


class TestMerge(TestWithFakeAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        return self.result

    def default_callback(self, _, _2, result):
        self.got_result = result
        TestWithFakeAgent.default_callback(self, _, _2, result)

    def test_run_ok_match_nok(self):
        self.result = {"result": "success"}
        self.got_result = None
        self.job_manager.new_job(Course('test').get_task('do_both'), {"problem_1": "1", "problem_2": "0"}, self.default_callback)
        self.wait_for_callback()
        assert "result" in self.got_result and self.got_result["result"] == "failed"

    def test_run_nok_match_ok(self):
        self.result = {"result": "failed"}
        self.got_result = None
        self.job_manager.new_job(Course('test').get_task('do_both'), {"problem_1": "0", "problem_2": "1"}, self.default_callback)
        self.wait_for_callback()
        assert "result" in self.got_result and self.got_result["result"] == "failed"

    def test_run_ok_match_ok(self):
        self.result = {"result": "success"}
        self.got_result = None
        self.job_manager.new_job(Course('test').get_task('do_both'), {"problem_1": "1", "problem_2": "1"}, self.default_callback)
        self.wait_for_callback()
        assert "result" in self.got_result and self.got_result["result"] == "success"