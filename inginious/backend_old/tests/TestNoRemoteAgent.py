# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


from inginious.backend.tests.TestJobManager import TestRemoteJobManager


class TestNoRemoteAgent(TestRemoteJobManager):
    def test_no_agent(self):
        assert self.job_manager.number_agents_available() == 0

    def test_run_job(self):
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "crash"
