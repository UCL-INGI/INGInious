# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


from inginious.backend.tests.TestJobManager import TestLocalJobManager
from inginious.common.hook_manager import HookManager


class TestHook(TestLocalJobManager):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        return {"result": "success"}

    def _hook(self, jobid, task, statinfo, inputdata):
        self.is_ok = inputdata == {"problem_id": "1"}

    def generate_hook_manager(self):
        hook_manager = HookManager()
        hook_manager.add_hook("new_job", self._hook)
        return hook_manager

    def test_ok(self):
        self.is_ok = False
        self.job_manager.new_job(self.course_factory.get_task('test', 'no_run'), {"problem_id": "1"}, self.default_callback)
        self.wait_for_callback()
        assert self.is_ok


class TestHookNoCrash(TestLocalJobManager):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        return {"result": "success"}

    def _hook(self, jobid, task, statinfo, inputdata):
        raise Exception("Run, you fools!")

    def generate_hook_manager(self):
        hook_manager = HookManager()
        hook_manager.add_hook("new_job", self._hook)
        return hook_manager

    def test_ok(self):
        self.job_manager.new_job(self.course_factory.get_task('test', 'no_run'), {"problem_id": "1"}, self.default_callback)
        self.wait_for_callback()
        assert self.got_callback_result["result"] == "success"

        # Twice to verify it still works after the first exception ;-)
        self.job_manager.new_job(self.course_factory.get_task('test', 'no_run'), {"problem_id": "1"}, self.default_callback)
        self.wait_for_callback()
        assert self.got_callback_result["result"] == "success"
