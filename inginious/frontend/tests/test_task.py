# pylint: disable=redefined-outer-name
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
from collections import OrderedDict

import pytest
import os

from inginious.common.filesystems.local import LocalFSProvider
from inginious.common.exceptions import InvalidNameException, TaskUnreadableException
from inginious.common.tasks_problems import *

from inginious.frontend.tasks import Task
from inginious.frontend.taskset_factory import create_factories
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.environment_types import register_base_env_types
from inginious.frontend.task_dispensers.toc import TableOfContents
from inginious.frontend.task_dispensers.combinatory_test import CombinatoryTest

task_dispensers = {TableOfContents.get_id(): TableOfContents, CombinatoryTest.get_id(): CombinatoryTest}
problem_types = {"code": CodeProblem, "code_single_line": CodeSingleLineProblem, "file": FileProblem,
                 "multiple_choice": MultipleChoiceProblem, "match": MatchProblem}


@pytest.fixture()
def ressource(request):
    register_base_env_types()
    fs = LocalFSProvider(os.path.join(os.path.dirname(__file__), 'tasks'))
    taskset_factory, course_factory, task_factory = create_factories(fs, task_dispensers, problem_types)
    yield taskset_factory, task_factory


class TestTaskBasic(object):

    def test_task_loading(self, ressource):
        '''Tests if a course file loads correctly'''
        taskset_factory, task_factory = ressource
        print("\033[1m-> common-tasks: task loading\033[0m")
        taskset = taskset_factory.get_taskset('test')
        t = task_factory.get_task(taskset, 'task1')
        assert t.get_environment_id() == 'default'
        assert t.get_id() == 'task1'
        assert t.get_response_type() == 'rst'

        env_param = t.get_environment_parameters()
        lim = env_param['limits']
        assert lim['disk'] == 100
        assert lim['memory'] == 32
        assert lim['time'] == 60

        assert t.get_problems()[0].get_type() == 'multiple_choice'

    def test_task_invalid_name(self, ressource):
        taskset_factory, task_factory = ressource
        try:
            taskset = taskset_factory.get_taskset('test')
            task_factory.get_task(taskset, 'invalid/name')
        except InvalidNameException:
            return
        assert False

    def test_task_invalid(self, ressource):
        taskset_factory, task_factory = ressource
        try:
            taskset = taskset_factory.get_taskset('test3')
            task_factory.get_task(taskset, 'invalid_task')
        except TaskUnreadableException:
            return
        assert False

    def test_no_problems(self, ressource):
        taskset_factory, task_factory = ressource
        try:
            Task(taskset_factory.get_taskset('test3'), 'invalid_task',
                 {"environment_id": "default",
                  "environment_type": "docker",
                  "environment_parameters": {
                      "run_cmd": '',
                      "limits": '0',
                      "time": '30',
                      "memory": '100',
                      "hard_time": '',
                  }
                  }, PluginManager(), problem_types)
        except Exception as e:
            assert str(e) == "Tasks must have some problems descriptions"
            return
        assert False

    def test_input_consistent_valid(self, ressource):
        taskset_factory, task_factory = ressource
        ts = taskset_factory.get_taskset("test")
        t = ts.get_task("task3")
        assert t.input_is_consistent({"unittest": "10"}, [], 0) is True

    def test_input_consistent_invalid(self, ressource):
        taskset_factory, task_factory = ressource
        ts = taskset_factory.get_taskset("test")
        t = ts.get_task("task3")
        assert t.input_is_consistent({"unittest": 10}, [], 0) is False


class TestTaskProblem(object):
    def test_problem_types(self, ressource):
        '''Tests if problem types are correctly recognized'''
        taskset_factory, task_factory = ressource
        ts = taskset_factory.get_taskset("test2")
        print("\033[1m-> common-tasks: problem types parsing\033[0m")
        t = task_factory.get_task(ts, 'task1')
        assert t.get_problems()[0].get_type() == 'match'

        t = task_factory.get_task(ts, 'task2')
        assert t.get_problems()[0].get_type() == 'match'

        t = task_factory.get_task(ts, 'task3')
        assert t.get_problems()[0].get_type() == 'multiple_choice'

    def test_multiple_choice(self, ressource):
        '''Tests multiple choice problems methods'''
        taskset_factory, task_factory = ressource
        ts = taskset_factory.get_taskset("test2")
        print("\033[1m-> common-tasks: multiple_choice parsing\033[0m")
        p = task_factory.get_task(ts, 'task3').get_problems()[0]
        assert p.allow_multiple()

        # Check correct and incorrect answer
        assert p.check_answer({'unittest': [0, 1]}, "")[0]
        assert not p.check_answer({'unittest': [0, 1, 2]}, "")[0]

        # Check random form input
        assert p.input_is_consistent({'unittest': [0, 1]}, [], 0)
        assert not p.input_is_consistent('test', [], 0)
        assert not p.input_is_consistent((10, 42), [], 0)

    def test_match(self, ressource):
        '''Tests match problems methods'''
        taskset_factory, task_factory = ressource
        ts = taskset_factory.get_taskset("test2")
        print("\033[1m-> common-tasks: match-problem loading\033[0m")
        p = task_factory.get_task(ts, 'task1').get_problems()[0]

        # Check correct and incorrect answer
        assert p.check_answer({'unittest': 'Answer 1'}, "")[0]
        assert not p.check_answer({'unittest': 'Wrong answer'}, "")[0]

        # Check random form input
        assert p.input_is_consistent({'unittest': 'Answer'}, [], 0)
        assert not p.input_is_consistent('test', [], 0)
        assert not p.input_is_consistent((10, 42), [], 0)

    def test_code(self, ressource):
        '''Tests code problems methods'''
        taskset_factory, task_factory = ressource
        ts = taskset_factory.get_taskset("test")
        print("\033[1m-> common-tasks: code problem parsing\033[0m")
        p = task_factory.get_task(ts, 'task3').get_problems()[0]

        # Check random form input
        assert p.input_is_consistent({'unittest': '10'}, [], 0)
        assert not p.input_is_consistent({'unittest/decimal': '10'}, [], 0)
        assert not p.input_is_consistent('test', [], 0)
        assert not p.input_is_consistent("ddd", [], 0)
        assert not p.input_is_consistent(42, [], 0)

    def test_file(self, ressource):
        """Tests file problems methods"""
        taskset_factory, task_factory = ressource
        ts = taskset_factory.get_taskset("test2")
        print("\033[1m-> common-tasks: file problem type\033[0m")
        p = task_factory.get_task(ts, 'task4').get_problems()[0]
        assert p.get_type() == 'file'

        # Check random form input
        assert p.input_is_consistent({"unittest": {"filename": "test.txt", "value": "test"}}, [".txt"], 100)
        assert not p.input_is_consistent({"unittest": {"filename": "test.txt", "value": "test"}}, [".nottxt"],
                                         100)
        assert not p.input_is_consistent({"unittest": {"filename": "test.txt", "value": "test"}}, [".txt"], 1)
        assert not p.input_is_consistent({"unittest": {"filename": "test.txt", "content": "test"}}, [".txt"],
                                         100)
        assert not p.input_is_consistent({"unittest": "text"}, [".txt"], 100)
