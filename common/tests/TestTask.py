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
import common.base
import common.courses
import common.tasks
import common.tasks_code_boxes

class test_tasks_basic(object):

    def test_task_loading(self):
        '''Tests if a course file loads correctly'''
        print "\033[1m-> common-tasks: task loading\033[0m"
        t = common.tasks.Task(common.courses.Course('test'), 'task1')
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
            common.tasks.Task(common.courses.Course('test'), 'invalid/name')
        except Exception as e:
            assert str(e)[0:21] == 'Task with invalid id:'
            return
        assert False

    def test_task_invalid(self):
        try:
            common.tasks.Task(common.courses.Course('test3'), 'invalid_task')
        except Exception as e:
            assert str(e)[0:30] == 'Error while reading task file:'
            return
        assert False

    def test_invalid_limits_1(self):
        try:
            t = common.tasks.Task(common.courses.Course('test3'), 'invalid_task', {"environment": "default", "limits":{"time":"a string!"}})
            a = t.get_limits()
            print a
        except Exception as e:
            assert str(e) == "Invalid limit"
            return
        assert False

    def test_invalid_limits_2(self):
        try:
            common.tasks.Task(common.courses.Course('test3'), 'invalid_task', {"environment": "default", "limits": {"time": -1}})
        except Exception as e:
            assert str(e) == "Invalid limit"
            return
        assert False

    def test_no_problems(self):
        try:
            common.tasks.Task(common.courses.Course('test3'), 'invalid_task', {"environment": "default"})
        except Exception as e:
            assert str(e) == "Tasks must have some problems descriptions"
            return
        assert False

    def test_course(self):
        #yeah, trivial. But we want 100% code coverage ;-)
        c = common.courses.Course("test")
        t = c.get_task("task1")
        assert t.get_course() == c
        assert t.get_course_id() == "test"

    def test_input_consistent_valid(self):
        c = common.courses.Course("test")
        t = c.get_task("task1")
        assert t.input_is_consistent({"unittest/decimal": "10"}) is True

    def test_input_consistent_invalid(self):
        c = common.courses.Course("test")
        t = c.get_task("task1")
        assert t.input_is_consistent({"unittest/decimal": "something"}) is False

    def test_check_answer_1(self):
        c = common.courses.Course("test")
        t = c.get_task("task1")
        valid, need_launch, main_message, problem_messages, multiple_choice_error_count = t.check_answer({"unittest/decimal": "10"})
        assert valid is True
        assert need_launch is True
        assert multiple_choice_error_count == 0

    def test_check_answer_2(self):
        c = common.courses.Course("test")
        t = c.get_task("task3")
        valid, need_launch, main_message, problem_messages, multiple_choice_error_count = t.check_answer({"unittest": ["0","1"]})
        assert valid is True
        assert need_launch is False
        assert multiple_choice_error_count == 0

    def test_check_answer_3(self):
        c = common.courses.Course("test")
        t = c.get_task("task3")
        valid, need_launch, main_message, problem_messages, multiple_choice_error_count = t.check_answer({"unittest": ["0"]})
        assert valid is False
        assert need_launch is False
        assert multiple_choice_error_count == 1

class test_tasks_problems(object):
    def test_problem_types(self):
        '''Tests if problem types are correctly recognized'''
        print "\033[1m-> common-tasks: problem types parsing\033[0m"
        t = common.tasks.Task(common.courses.Course('test2'), 'task1')
        assert t.get_problems()[0].get_type() == 'match'
        
        t = common.tasks.Task(common.courses.Course('test2'), 'task2')
        assert t.get_problems()[0].get_type() == 'match'
        
        t = common.tasks.Task(common.courses.Course('test2'), 'task3')
        assert t.get_problems()[0].get_type() == 'multiple-choice'
    
    def test_multiple_choice(self):
        '''Tests multiple choice problems methods'''
        print "\033[1m-> common-tasks: multiple-choice parsing\033[0m"
        p = common.tasks.Task(common.courses.Course('test2'), 'task3').get_problems()[0]
        assert p.allow_multiple()
        
        # Check correct and incorrect answer
        assert p.check_answer({'unittest':[0,1]})[0]
        assert not p.check_answer({'unittest':[0,1,2]})[0]
        
        # Check random form input
        assert p.input_is_consistent({'unittest':[0,1]})
        assert not p.input_is_consistent('test')
        assert not p.input_is_consistent((10, 42))
    
    def test_match(self):
        '''Tests match problems methods'''
        print "\033[1m-> common-tasks: match-problem loading\033[0m"
        p = common.tasks.Task(common.courses.Course('test2'), 'task1').get_problems()[0]
        
        # Check correct and incorrect answer
        assert p.check_answer({'unittest':'Answer 1'})[0]
        assert not p.check_answer({'unittest':'Wrong answer'})[0]
        
        # Check random form input
        assert p.input_is_consistent({'unittest':'Answer'})
        assert not p.input_is_consistent('test')
        assert not p.input_is_consistent((10, 42))
    
    def test_code(self):
        '''Tests code problems methods'''
        print "\033[1m-> common-tasks: code-problem parsing\033[0m"
        p = common.tasks.Task(common.courses.Course('test'), 'task1').get_problems()[0]
        
        # Check random form input
        assert p.input_is_consistent({'unittest/decimal':'10'})
        assert not p.input_is_consistent('test')
        assert not p.input_is_consistent({'unittest':'10'})

class test_tasks_boxes(object):
    def test_number_boxes(self):
        '''Tests if get_boxes returns the correct number of boxes'''
        print "\033[1m-> common-tasks: problem boxes count\033[0m"
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        assert len(p.get_boxes()) == 12
    
    def test_filebox(self):
        '''Tests filebox methods'''
        print "\033[1m-> common-tasks: filebox problem type\033[0m"
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[11]
        assert box.get_type() == 'file'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/file1": {"filename":"test.txt", "value":"test"}})
        assert not box.input_is_consistent({"unittest/file1": {"filename":"test.txt", "content":"test"}})
        assert not box.input_is_consistent("test")
    
    def test_integer_inputbox(self):
        '''Tests integer inputbox methods'''
        print "\033[1m-> common-tasks: integer box problem type\033[0m"
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[1]
        assert box.get_type() == 'input' and box._input_type =='integer'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/int1": "42"})
        assert not box.input_is_consistent({"unittest/int1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
    
    def test_decimal_inputbox(self):
        '''Tests decimal inputbox methods'''
        print "\033[1m-> common-tasks: decimal box problem type\033[0m"
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[3]
        assert box.get_type() == 'input' and box._input_type =='decimal'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/decimal1": "42.3"})
        assert not box.input_is_consistent({"unittest/decimal1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
    
    def test_text_inputbox(self):
        '''Tests text inputbox methods'''
        print "\033[1m-> common-tasks: text-input box problem type\033[0m"
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[5]
        assert box.get_type() == 'input' and box._input_type =='text'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/text1": "42.3"})
        assert box.input_is_consistent({"unittest/text1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
    
    def test_multiline_inputbox(self):
        '''Tests multiline inputbox methods'''
        print "\033[1m-> common-tasks: multiline box problem type\033[0m"
        p = common.tasks.Task(common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[8]
        assert box.get_type() == 'multiline'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/code1": "42.3"})
        assert box.input_is_consistent({"unittest/code1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)