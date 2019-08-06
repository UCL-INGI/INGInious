# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os

import inginious.common.base
import inginious.common.tasks
from inginious.common.filesystems.local import LocalFSProvider
from inginious.common.exceptions import InvalidNameException, TaskUnreadableException
from inginious.common.hook_manager import HookManager
from inginious.common.tasks_problems import *
from inginious.common.task_factory import TaskFactory

problem_types = {"code": CodeProblem, "code_single_line": CodeSingleLineProblem, "file": FileProblem,
                         "multiple_choice": MultipleChoiceProblem, "match": MatchProblem}

class test_tasks_basic(object):
    def setUp(self):
        fs = LocalFSProvider(os.path.join(os.path.dirname(__file__), 'tasks'))
        self.task_factory = TaskFactory(fs, HookManager(), problem_types)

    def test_task_loading(self):
        '''Tests if a course file loads correctly'''
        print("\033[1m-> common-tasks: task loading\033[0m")
        t = self.task_factory.get_task('test', 'task1')
        assert t.get_environment() == 'default'
        assert t.get_id() == 'task1'
        assert t.get_courseid() == 'test'
        assert t.get_response_type() == 'rst'

        lim = t.get_limits()
        assert lim['disk'] == 100
        assert lim['memory'] == 32
        assert lim['time'] == 60

        assert t.get_problems()[0].get_type() == 'multiple_choice'

    def test_task_invalid_name(self):
        try:
            self.task_factory.get_task('test', 'invalid/name')
        except InvalidNameException:
            return
        assert False

    def test_task_invalid(self):
        try:
            self.task_factory.get_task('test3', 'invalid_task')
        except TaskUnreadableException:
            return
        assert False

    def test_invalid_limits_1(self):
        try:
            t = inginious.common.tasks.Task('test3', 'invalid_task',
                                            {"environment": "default", "limits": {"time": "a string!"}},
                                            'fake_path', None, HookManager(), problem_types)
            a = t.get_limits()
            print(a)
        except Exception as e:
            assert str(e) == "Invalid limit"
            return
        assert False

    def test_invalid_limits_2(self):
        try:
            inginious.common.tasks.Task('test3', 'invalid_task',
                                        {"environment": "default", "limits": {"time": -1}}, 'fake_path', None, HookManager(), problem_types)
        except Exception as e:
            assert str(e) == "Invalid limit"
            return
        assert False

    def test_no_problems(self):
        try:
            inginious.common.tasks.Task('test3', 'invalid_task', {"environment": "default"}, 'fake_path', None, HookManager(), problem_types)
        except Exception as e:
            assert str(e) == "Tasks must have some problems descriptions"
            return
        assert False

    def test_course(self):
        # yeah, trivial. But we want 100% code coverage ;-)
        t = self.task_factory.get_task("test", "task1")
        assert t.get_courseid() == "test"

    def test_input_consistent_valid(self):
        t = self.task_factory.get_task("test", "task3")
        assert t.input_is_consistent({"unittest": "10"}, [], 0) is True

    def test_input_consistent_invalid(self):
        t = self.task_factory.get_task("test", "task3")
        assert t.input_is_consistent({"unittest": 10}, [], 0) is False

    def test_check_answer_1(self):
        t = self.task_factory.get_task("test", "task1")
        valid, need_launch, main_message, problem_messages, error_count, multiple_choice_error_count = t.check_answer({"unittest": ["0", "1"]}, "")
        assert valid is True
        assert need_launch is False
        assert error_count == 0
        assert multiple_choice_error_count == 0

    def test_check_answer_2(self):
        t = self.task_factory.get_task("test", "task1")
        valid, need_launch, main_message, problem_messages, error_count, multiple_choice_error_count = t.check_answer({"unittest": ["0"]}, "")
        assert valid is False
        assert need_launch is False
        assert error_count == 1
        assert multiple_choice_error_count == 1


class test_tasks_problems(object):
    def setUp(self):
        fs = LocalFSProvider(os.path.join(os.path.dirname(__file__), 'tasks'))
        self.task_factory = TaskFactory(fs, None, problem_types)

    def test_problem_types(self):
        '''Tests if problem types are correctly recognized'''
        print("\033[1m-> common-tasks: problem types parsing\033[0m")
        t = self.task_factory.get_task('test2', 'task1')
        assert t.get_problems()[0].get_type() == 'match'

        t = self.task_factory.get_task('test2', 'task2')
        assert t.get_problems()[0].get_type() == 'match'

        t = self.task_factory.get_task('test2', 'task3')
        assert t.get_problems()[0].get_type() == 'multiple_choice'

    def test_multiple_choice(self):
        '''Tests multiple choice problems methods'''
        print("\033[1m-> common-tasks: multiple_choice parsing\033[0m")
        p = self.task_factory.get_task('test2', 'task3').get_problems()[0]
        assert p.allow_multiple()

        # Check correct and incorrect answer
        assert p.check_answer({'unittest': [0, 1]}, "")[0]
        assert not p.check_answer({'unittest': [0, 1, 2]}, "")[0]

        # Check random form input
        assert p.input_is_consistent({'unittest': [0, 1]}, [], 0)
        assert not p.input_is_consistent('test', [], 0)
        assert not p.input_is_consistent((10, 42), [], 0)

    def test_match(self):
        '''Tests match problems methods'''
        print("\033[1m-> common-tasks: match-problem loading\033[0m")
        p = self.task_factory.get_task('test2', 'task1').get_problems()[0]

        # Check correct and incorrect answer
        assert p.check_answer({'unittest': 'Answer 1'}, "")[0]
        assert not p.check_answer({'unittest': 'Wrong answer'}, "")[0]

        # Check random form input
        assert p.input_is_consistent({'unittest': 'Answer'}, [], 0)
        assert not p.input_is_consistent('test', [], 0)
        assert not p.input_is_consistent((10, 42), [], 0)

    def test_code(self):
        '''Tests code problems methods'''
        print("\033[1m-> common-tasks: code problem parsing\033[0m")
        p = self.task_factory.get_task('test', 'task3').get_problems()[0]

        # Check random form input
        assert p.input_is_consistent({'unittest': '10'}, [], 0)
        assert not p.input_is_consistent({'unittest/decimal': '10'}, [], 0)
        assert not p.input_is_consistent('test', [], 0)
        assert not p.input_is_consistent("ddd", [], 0)
        assert not p.input_is_consistent(42, [], 0)

    def test_file(self):
        '''Tests file problems methods'''
        print("\033[1m-> common-tasks: file problem type\033[0m")
        p = self.task_factory.get_task('test2', 'task4').get_problems()[0]
        assert p.get_type() == 'file'

        # Check random form input
        assert p.input_is_consistent({"unittest": {"filename": "test.txt", "value": "test"}}, [".txt"], 100)
        assert not p.input_is_consistent({"unittest": {"filename": "test.txt", "value": "test"}}, [".nottxt"],
                                           100)
        assert not p.input_is_consistent({"unittest": {"filename": "test.txt", "value": "test"}}, [".txt"], 1)
        assert not p.input_is_consistent({"unittest": {"filename": "test.txt", "content": "test"}}, [".txt"],
                                           100)
        assert not p.input_is_consistent({"unittest": "text"}, [".txt"], 100)
