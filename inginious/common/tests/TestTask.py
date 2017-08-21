# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os

import inginious.common.base
import inginious.common.courses
import inginious.common.tasks
import inginious.common.tasks_code_boxes
from inginious.common.filesystems.local import LocalFSProvider
from inginious.common.course_factory import create_factories
from inginious.common.exceptions import InvalidNameException, TaskUnreadableException
from inginious.common.hook_manager import HookManager


class test_tasks_basic(object):
    def setUp(self):
        fs = LocalFSProvider(os.path.join(os.path.dirname(__file__), 'tasks'))
        self.course_factory, _ = create_factories(fs)

    def test_task_loading(self):
        '''Tests if a course file loads correctly'''
        print("\033[1m-> common-tasks: task loading\033[0m")
        t = self.course_factory.get_task('test', 'task1')
        assert t.get_environment() == 'default'
        assert t.get_id() == 'task1'
        assert t.get_course_id() == 'test'
        assert t.get_response_type() == 'rst'

        lim = t.get_limits()
        assert lim['disk'] == 100
        assert lim['memory'] == 32
        assert lim['time'] == 60

        assert t.get_problems()[0].get_type() == 'code'

    def test_task_invalid_name(self):
        try:
            self.course_factory.get_task('test', 'invalid/name')
        except InvalidNameException:
            return
        assert False

    def test_task_invalid(self):
        try:
            self.course_factory.get_task('test3', 'invalid_task')
        except TaskUnreadableException:
            return
        assert False

    def test_invalid_limits_1(self):
        try:
            t = inginious.common.tasks.Task(self.course_factory.get_course('test3'), 'invalid_task',
                                            {"environment": "default", "limits": {"time": "a string!"}},
                                            'fake_path', HookManager())
            a = t.get_limits()
            print(a)
        except Exception as e:
            assert str(e) == "Invalid limit"
            return
        assert False

    def test_invalid_limits_2(self):
        try:
            inginious.common.tasks.Task(self.course_factory.get_course('test3'), 'invalid_task',
                                        {"environment": "default", "limits": {"time": -1}}, 'fake_path', HookManager())
        except Exception as e:
            assert str(e) == "Invalid limit"
            return
        assert False

    def test_no_problems(self):
        try:
            inginious.common.tasks.Task(self.course_factory.get_course('test3'), 'invalid_task', {"environment": "default"}, 'fake_path', HookManager())
        except Exception as e:
            assert str(e) == "Tasks must have some problems descriptions"
            return
        assert False

    def test_course(self):
        # yeah, trivial. But we want 100% code coverage ;-)
        c = self.course_factory.get_course("test")
        t = c.get_task("task1")
        assert t.get_course() == c
        assert t.get_course_id() == "test"

    def test_input_consistent_valid(self):
        c = self.course_factory.get_course("test")
        t = c.get_task("task1")
        assert t.input_is_consistent({"unittest/decimal": "10"}, [], 0) is True

    def test_input_consistent_invalid(self):
        c = self.course_factory.get_course("test")
        t = c.get_task("task1")
        assert t.input_is_consistent({"unittest/decimal": "something"}, [], 0) is False

    def test_check_answer_1(self):
        c = self.course_factory.get_course("test")
        t = c.get_task("task1")
        valid, need_launch, main_message, problem_messages, error_count, multiple_choice_error_count = t.check_answer({"unittest/decimal": "10"})
        assert valid is True
        assert need_launch is True
        assert error_count == 0
        assert multiple_choice_error_count == 0

    def test_check_answer_2(self):
        c = self.course_factory.get_course("test")
        t = c.get_task("task3")
        valid, need_launch, main_message, problem_messages, error_count, multiple_choice_error_count = t.check_answer({"unittest": ["0", "1"]})
        assert valid is True
        assert need_launch is False
        assert error_count == 0
        assert multiple_choice_error_count == 0

    def test_check_answer_3(self):
        c = self.course_factory.get_course("test")
        t = c.get_task("task3")
        valid, need_launch, main_message, problem_messages, error_count, multiple_choice_error_count = t.check_answer({"unittest": ["0"]})
        assert valid is False
        assert need_launch is False
        assert error_count == 1
        assert multiple_choice_error_count == 1


class test_tasks_problems(object):
    def setUp(self):
        fs = LocalFSProvider(os.path.join(os.path.dirname(__file__), 'tasks'))
        self.course_factory, _ = create_factories(fs)

    def test_problem_types(self):
        '''Tests if problem types are correctly recognized'''
        print("\033[1m-> common-tasks: problem types parsing\033[0m")
        t = self.course_factory.get_task('test2', 'task1')
        assert t.get_problems()[0].get_type() == 'match'

        t = self.course_factory.get_task('test2', 'task2')
        assert t.get_problems()[0].get_type() == 'match'

        t = self.course_factory.get_task('test2', 'task3')
        assert t.get_problems()[0].get_type() == 'multiple-choice'

    def test_multiple_choice(self):
        '''Tests multiple choice problems methods'''
        print("\033[1m-> common-tasks: multiple-choice parsing\033[0m")
        p = self.course_factory.get_task('test2', 'task3').get_problems()[0]
        assert p.allow_multiple()

        # Check correct and incorrect answer
        assert p.check_answer({'unittest': [0, 1]})[0]
        assert not p.check_answer({'unittest': [0, 1, 2]})[0]

        # Check random form input
        assert p.input_is_consistent({'unittest': [0, 1]}, [], 0)
        assert not p.input_is_consistent('test', [], 0)
        assert not p.input_is_consistent((10, 42), [], 0)

    def test_match(self):
        '''Tests match problems methods'''
        print("\033[1m-> common-tasks: match-problem loading\033[0m")
        p = self.course_factory.get_task('test2', 'task1').get_problems()[0]

        # Check correct and incorrect answer
        assert p.check_answer({'unittest': 'Answer 1'})[0]
        assert not p.check_answer({'unittest': 'Wrong answer'})[0]

        # Check random form input
        assert p.input_is_consistent({'unittest': 'Answer'}, [], 0)
        assert not p.input_is_consistent('test', [], 0)
        assert not p.input_is_consistent((10, 42), [], 0)

    def test_code(self):
        '''Tests code problems methods'''
        print("\033[1m-> common-tasks: code-problem parsing\033[0m")
        p = self.course_factory.get_task('test', 'task1').get_problems()[0]

        # Check random form input
        assert p.input_is_consistent({'unittest/decimal': '10'}, [], 0)
        assert not p.input_is_consistent('test', [], 0)
        assert not p.input_is_consistent({'unittest': '10'}, [], 0)


class test_tasks_boxes(object):
    def setUp(self):
        fs = LocalFSProvider(os.path.join(os.path.dirname(__file__), 'tasks'))
        self.course_factory, _ = create_factories(fs)

    def test_number_boxes(self):
        '''Tests if get_boxes returns the correct number of boxes'''
        print("\033[1m-> common-tasks: problem boxes count\033[0m")
        p = self.course_factory.get_task('test2', 'task4').get_problems()[0]
        assert len(p.get_boxes()) == 12

    def test_filebox(self):
        '''Tests filebox methods'''
        print("\033[1m-> common-tasks: filebox problem type\033[0m")
        p = self.course_factory.get_task('test2', 'task4').get_problems()[0]
        box = p.get_boxes()[11]
        assert box.get_type() == 'file'

        # Check random form input
        assert box.input_is_consistent({"unittest/file1": {"filename": "test.txt", "value": "test"}}, [".txt"], 100)
        assert not box.input_is_consistent({"unittest/file1": {"filename": "test.txt", "value": "test"}}, [".nottxt"], 100)
        assert not box.input_is_consistent({"unittest/file1": {"filename": "test.txt", "value": "test"}}, [".txt"], 1)
        assert not box.input_is_consistent({"unittest/file1": {"filename": "test.txt", "content": "test"}}, [".txt"], 100)
        assert not box.input_is_consistent({"unittest/file1": "text"}, [".txt"], 100)

    def test_integer_inputbox(self):
        '''Tests integer inputbox methods'''
        print("\033[1m-> common-tasks: integer box problem type\033[0m")
        p = self.course_factory.get_task('test2', 'task4').get_problems()[0]
        box = p.get_boxes()[1]
        assert box.get_type() == 'input' and box._input_type == 'integer'

        # Check random form input
        assert box.input_is_consistent({"unittest/int1": "42"}, [], 0)
        assert not box.input_is_consistent({"unittest/int1": "test"}, [], 0)
        assert not box.input_is_consistent("ddd", [], 0)
        assert not box.input_is_consistent(42, [], 0)

    def test_decimal_inputbox(self):
        '''Tests decimal inputbox methods'''
        print("\033[1m-> common-tasks: decimal box problem type\033[0m")
        p = self.course_factory.get_task('test2', 'task4').get_problems()[0]
        box = p.get_boxes()[3]
        assert box.get_type() == 'input' and box._input_type == 'decimal'

        # Check random form input
        assert box.input_is_consistent({"unittest/decimal1": "42.3"}, [], 0)
        assert not box.input_is_consistent({"unittest/decimal1": "test"}, [], 0)
        assert not box.input_is_consistent("ddd", [], 0)
        assert not box.input_is_consistent(42, [], 0)

    def test_text_inputbox(self):
        '''Tests text inputbox methods'''
        print("\033[1m-> common-tasks: text-input box problem type\033[0m")
        p = self.course_factory.get_task('test2', 'task4').get_problems()[0]
        box = p.get_boxes()[5]
        assert box.get_type() == 'input' and box._input_type == 'text'

        # Check random form input
        assert box.input_is_consistent({"unittest/text1": "42.3"}, [], 0)
        assert box.input_is_consistent({"unittest/text1": "test"}, [], 0)
        assert not box.input_is_consistent("ddd", [], 0)
        assert not box.input_is_consistent(42, [], 0)

    def test_multiline_inputbox(self):
        '''Tests multiline inputbox methods'''
        print("\033[1m-> common-tasks: multiline box problem type\033[0m")
        p = self.course_factory.get_task('test2', 'task4').get_problems()[0]
        box = p.get_boxes()[8]
        assert box.get_type() == 'multiline'

        # Check random form input
        assert box.input_is_consistent({"unittest/code1": "42.3"}, [], 0)
        assert box.input_is_consistent({"unittest/code1": "test"}, [], 0)
        assert not box.input_is_consistent("ddd", [], 0)
        assert not box.input_is_consistent(42, [], 0)
