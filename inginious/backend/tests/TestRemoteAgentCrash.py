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
""" Theses tests checks that the inginious.backend is bad-agent-proof """

import time

from inginious.backend.tests.TestJobManager import TestWithFakeRemoteAgent


class TestRemoteAgentJobCrash(TestWithFakeRemoteAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        raise Exception("You shall not pass!")

    def test_exception_job(self):
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "crash"


class TestRemoteAgentAliasUpdateCrash(TestWithFakeRemoteAgent):
    def update_image_aliases_func(self, image_aliases):
        raise Exception("Pass, you shall not.")

    def test_exception_alias(self):
        time.sleep(2)  # allow the exception to propagate through the different thread linked via RPyC
        # If this, runs, it's ok!
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"


class TestRemoteAgentTaskUpdateCrash1(TestWithFakeRemoteAgent):
    def get_task_directory_hashes_func(self):
        raise Exception(".")

    def test_exception_task_1(self):
        time.sleep(2)  # allow the exception to propagate through the different thread linked via RPyC
        # If this, runs, it's ok!
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"


class TestRemoteAgentTaskUpdateCrash2(TestWithFakeRemoteAgent):
    def update_task_directory_func(self, remote_tar_file, to_delete):
        raise Exception(".")

    def test_exception_task_2(self):
        time.sleep(5)  # allow the exception to propagate through the different thread linked via RPyC

        # If this, runs, it's ok!
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result
        assert result["result"] == "success"
