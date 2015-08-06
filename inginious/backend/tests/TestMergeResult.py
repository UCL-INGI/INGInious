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
from inginious.backend.job_managers.abstract import AbstractJobManager


class TestNotInAgent(TestLocalJobManager):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        self.was_in = True
        return {"result": "success"}

    def test_ok(self):
        self.was_in = False
        self.job_manager.new_job(self.course_factory.get_task('test', 'no_run'), {"problem_id": "1"}, self.default_callback)
        self.wait_for_callback()
        assert not self.was_in

    def test_fail(self):
        self.was_in = False
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_id": "1"}, self.default_callback)
        self.wait_for_callback()
        assert self.was_in


class TestManualMerge(object):
    def test_norun_merge_list(self):
        res = AbstractJobManager._merge_results({"result": "success", "problems": {"id1": ["a", "a"]}, "text": ["b", "b"]}, None)
        assert res["problems"]["id1"] == "a\na"
        assert res["text"] == "b\nb"

    def test_neg_grades(self):
        res = AbstractJobManager._merge_results({"result": "success", "grade": -8}, None)
        assert res["grade"] == 0

    def test_too_high_grades(self):
        res = AbstractJobManager._merge_results({"result": "success", "grade": 100000}, None)
        assert res["grade"] == 200

    def test_non_float_grades(self):
        res = AbstractJobManager._merge_results({"result": "success", "grade": "You shall not grade!"}, None)
        assert res["grade"] == 0

    def test_std_out_err(self):
        res = AbstractJobManager._merge_results({"result": "success"}, {"result": "success", "stdout": "a", "stderr": "b"})
        assert res["stdout"] == "a"
        assert res["stderr"] == "b"

    def test_strange_result_types(self):
        res = AbstractJobManager._merge_results({"result": "success"}, {"result": "strange"})
        assert res["result"] == "error"

    def test_merge_text_problem(self):
        res = AbstractJobManager._merge_results({"result": "success", "problems": {"id": "a"}}, {"result": "success", "problems": {"id": "b"}})
        assert res["problems"]["id"] == "b\na"

    def test_merge_text_global(self):
        res = AbstractJobManager._merge_results({"result": "success", "text": "a"}, {"result": "success", "text": "b"})
        assert res["text"] == "b\na"


class TestAutoMerge(TestLocalJobManager):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        return self.result

    def test_run_ok_match_nok(self):
        self.result = {"result": "success"}
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_both'), {"problem_1": "1", "problem_2": "0"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "failed"

    def test_run_nok_match_ok(self):
        self.result = {"result": "failed"}
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_both'), {"problem_1": "0", "problem_2": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "failed"

    def test_run_ok_match_ok(self):
        self.result = {"result": "success"}
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_both'), {"problem_1": "1", "problem_2": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"

    def test_merge_text(self):
        self.result = {"result": "success", "problems": {"problem_1": 'a'}}
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_both'), {"problem_1": "1", "problem_2": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "result" in result and result["result"] == "success"
        assert "problems" in result
        assert "problem_1" in result["problems"] and "problem_2" in result["problems"]
        assert result["problems"]["problem_1"] == "a"
        assert result["problems"]["problem_2"] == "Correct answer"

    def test_grade_no_run_success(self):
        self.result = {"result": "failed"}  # should not be checked!
        self.job_manager.new_job(self.course_factory.get_task('test', 'no_run'), {"problem_id": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "grade" in result and result["grade"] == 100.0

    def test_grade_no_run_failed(self):
        self.result = {"result": "success"}
        self.job_manager.new_job(self.course_factory.get_task('test', 'no_run'), {"problem_id": "0"}, self.default_callback)
        result = self.wait_for_callback()
        assert "grade" in result and result["grade"] == 0

    def test_grade_do_run_success(self):
        self.result = {"result": "success"}
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_id": "0"}, self.default_callback)
        result = self.wait_for_callback()
        assert "grade" in result and result["grade"] == 100.0

    def test_grade_do_run_failed(self):
        self.result = {"result": "failed"}
        self.job_manager.new_job(self.course_factory.get_task('test', 'do_run'), {"problem_id": "0"}, self.default_callback)
        result = self.wait_for_callback()
        assert "grade" in result and result["grade"] == 0

    def test_mcq(self):
        self.result = {"result": "success"}
        self.job_manager.new_job(self.course_factory.get_task('test', 'no_run_mcq'), {"mcq1": "1", "mcq2": "1"}, self.default_callback)
        result = self.wait_for_callback()
        assert "grade" in result and result["grade"] == 100.0

    def test_mcq_fail(self):
        self.result = {"result": "success"}
        self.job_manager.new_job(self.course_factory.get_task('test', 'no_run_mcq'), {"mcq1": "2", "mcq2": "3"}, self.default_callback)
        result = self.wait_for_callback()
        assert "grade" in result and result["grade"] == 0
