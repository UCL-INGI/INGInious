# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
import unittest

from tests import *
import inginious.common.base
import inginious.common.courses
import inginious.common.tasks
import inginious.common.tasks_code_boxes
class common_tasks_basic(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_task_loading(self):
        '''Tests if a course file loads correctly'''
        print "\033[1m-> inginious.common-tasks: task loading\033[0m"
        t = inginious.common.tasks.Task(inginious.common.courses.Course('test'), 'task1')
        assert t.get_environment() == 'default'
        assert t.get_id() == 'task1'
        assert t.get_course_id() == 'test'
        assert t.get_response_type() == 'rst'
        
        lim = t.get_limits()
        assert lim['disk'] == 100
        assert lim['memory'] == 32
        assert lim['time'] == 60
        
        assert t.get_problems()[0].get_type() == 'code'
    
    def tearDown(self):
        pass

class common_tasks_problems(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_problem_types(self):
        '''Tests if problem types are correctly recognized'''
        print "\033[1m-> inginious.common-tasks: problem types parsing\033[0m"
        t = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task1')
        assert t.get_problems()[0].get_type() == 'match'
        
        t = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task2')
        assert t.get_problems()[0].get_type() == 'match'
        
        t = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task3')
        assert t.get_problems()[0].get_type() == 'multiple-choice'
    
    def test_multiple_choice(self):
        '''Tests multiple choice problems methods'''
        print "\033[1m-> inginious.common-tasks: multiple-choice parsing\033[0m"
        p = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task3').get_problems()[0]
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
        print "\033[1m-> inginious.common-tasks: match-problem loading\033[0m"
        p = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task1').get_problems()[0]
        
        # Check correct and incorrect answer
        assert p.check_answer({'unittest':'Answer 1'})[0]
        assert not p.check_answer({'unittest':'Wrong answer'})[0]
        
        # Check random form input
        assert p.input_is_consistent({'unittest':'Answer'})
        assert not p.input_is_consistent('test')
        assert not p.input_is_consistent((10, 42))
    
    def test_code(self):
        '''Tests code problems methods'''
        print "\033[1m-> inginious.common-tasks: code-problem parsing\033[0m"
        p = inginious.common.tasks.Task(inginious.common.courses.Course('test'), 'task1').get_problems()[0]
        
        # Check random form input
        assert p.input_is_consistent({'unittest/decimal':'10'})
        assert not p.input_is_consistent('test')
        assert not p.input_is_consistent({'unittest':'10'})
        
    def tearDown(self):
        pass

class common_tasks_boxes(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_number_boxes(self):
        '''Tests if get_boxes returns the correct number of boxes'''
        print "\033[1m-> inginious.common-tasks: problem boxes count\033[0m"
        p = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task4').get_problems()[0]
        assert len(p.get_boxes()) == 12
    
    def test_filebox(self):
        '''Tests filebox methods'''
        print "\033[1m-> inginious.common-tasks: filebox problem type\033[0m"
        p = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[11]
        assert box.get_type() == 'file'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/file1": {"filename":"test.txt", "value":"test"}})
        assert not box.input_is_consistent({"unittest/file1": {"filename":"test.txt", "content":"test"}})
        assert not box.input_is_consistent("test")
    
    def test_integer_inputbox(self):
        '''Tests integer inputbox methods'''
        print "\033[1m-> inginious.common-tasks: integer box problem type\033[0m"
        p = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[1]
        assert box.get_type() == 'input' and box._input_type =='integer'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/int1": "42"})
        assert not box.input_is_consistent({"unittest/int1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
    
    def test_decimal_inputbox(self):
        '''Tests decimal inputbox methods'''
        print "\033[1m-> inginious.common-tasks: decimal box problem type\033[0m"
        p = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[3]
        assert box.get_type() == 'input' and box._input_type =='decimal'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/decimal1": "42.3"})
        assert not box.input_is_consistent({"unittest/decimal1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
    
    def test_text_inputbox(self):
        '''Tests text inputbox methods'''
        print "\033[1m-> inginious.common-tasks: text-input box problem type\033[0m"
        p = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[5]
        assert box.get_type() == 'input' and box._input_type =='text'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/text1": "42.3"})
        assert box.input_is_consistent({"unittest/text1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
    
    def test_multiline_inputbox(self):
        '''Tests multiline inputbox methods'''
        print "\033[1m-> inginious.common-tasks: multiline box problem type\033[0m"
        p = inginious.common.tasks.Task(inginious.common.courses.Course('test2'), 'task4').get_problems()[0]
        box = p.get_boxes()[8]
        assert box.get_type() == 'multiline'
        
        # Check random form input
        assert box.input_is_consistent({"unittest/code1": "42.3"})
        assert box.input_is_consistent({"unittest/code1": "test"})
        assert not box.input_is_consistent("ddd")
        assert not box.input_is_consistent(42)
        
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not inginious.common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> inginious.common-tasks: tests cannot be run remotely\033[0m"
