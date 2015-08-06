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

import time

from inginious.backend.tests.TestJobManager import TestWithFakeRemoteAgent


class TestRemoteAgentOK(TestWithFakeRemoteAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        return {"result": "success", "grade": 100.0}

    def get_task_directory_hashes_func(self):
        return {"todelete": ("a random invalid hash", 3456)}

    def update_task_directory_func(self, remote_tar_file, to_delete):
        self.remote_tar_file = remote_tar_file
        self.nb_calls = self.nb_calls + 1
        if self.nb_calls == 1:
            self.to_delete1 = to_delete
        elif self.nb_calls == 2:
            self.to_delete2 = to_delete

    def test_job(self):
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_1": "1"}, self.default_callback)
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
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_1": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"
