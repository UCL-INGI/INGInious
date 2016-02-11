# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


import time

from inginious.backend.helpers.job_manager_buffer import JobManagerBuffer
from inginious.backend.helpers.job_manager_sync import JobManagerSync
from inginious.backend.tests.TestJobManager import TestLocalJobManager


class TestSync(TestLocalJobManager):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        return {"result": "success"}

    def test_sync(self):
        jbs = JobManagerSync(self.job_manager)
        result = jbs.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_id": "0"})
        assert "result" in result and result["result"] == "success"


class TestBuffer(TestLocalJobManager):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        time.sleep(1)
        return {"result": "success"}

    def test_is_waiting(self):
        jbb = JobManagerBuffer(self.job_manager)
        jobid1 = jbb.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_id": "0"})
        assert jbb.is_waiting(jobid1)
        time.sleep(2)
        assert jbb.get_result(jobid1)["result"] == "success"

    def test_is_done(self):
        jbb = JobManagerBuffer(self.job_manager)
        jobid1 = jbb.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_id": "0"})
        time.sleep(2)
        assert jbb.is_done(jobid1)
        assert jbb.get_result(jobid1)["result"] == "success"
