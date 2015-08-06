# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.

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
