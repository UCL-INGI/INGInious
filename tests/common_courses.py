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
class common_courses(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_course_loading(self):
        '''Tests if a course file loads correctly'''
        print "\033[1m-> inginious.common-courses: course loading\033[0m"
        c = inginious.common.courses.Course('test')
        assert c.get_id() == 'test'
        assert c._content['accessible'] == None
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 1'
        
        c = inginious.common.courses.Course('test2')
        assert c.get_id() == 'test2'
        assert c._content['accessible'] == '1970-01-01/2033-01-01'
        assert c._content['admins'] == ['testadmin1']
        assert c._content['name'] == 'Unit test 2'
        
        c = inginious.common.courses.Course('test3')
        assert c.get_id() == 'test3'
        assert c._content['accessible'] == '1970-01-01/1970-12-31'
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 3'
    
    def test_all_courses_loading(self):
        '''Tests if all courses are loaded by Course.get_all_courses()'''
        print "\033[1m-> inginious.common-courses: all courses loading\033[0m"
        c = inginious.common.courses.Course.get_all_courses()
        assert 'test' in c
        assert 'test2' in c
        assert 'test3' in c
    
    def test_tasks_loading(self):
        '''Tests loading tasks from the get_tasks method'''
        print "\033[1m-> inginious.common-courses: course tasks loading\033[0m"
        c = inginious.common.courses.Course('test')
        t = c.get_tasks()
        assert 'task1' in t
        assert 'task2' in t
        assert 'task3' in t
        assert 'task4' in t
        
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not inginious.common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> inginious.common-courses: tests cannot be run remotely\033[0m"
