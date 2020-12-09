# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import tempfile
import shutil

from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.course_factory import create_factories
from inginious.common.tasks_problems import *
from inginious.frontend.task_dispensers.toc import TableOfContents
from inginious.frontend.environment_types import register_base_env_types
from inginious.frontend.task_dispensers.combinatory_test import CombinatoryTest

task_dispensers = {TableOfContents.get_id(): TableOfContents, CombinatoryTest.get_id(): CombinatoryTest}
problem_types = {"code": CodeProblem, "code_single_line": CodeSingleLineProblem, "file": FileProblem,
                 "multiple_choice": MultipleChoiceProblem, "match": MatchProblem}

class TestCourse(object):
    def setUp(self):
        register_base_env_types()
        fs = LocalFSProvider(os.path.join(os.path.dirname(__file__), 'tasks'))
        self.course_factory, _ = create_factories(fs, task_dispensers, problem_types)

    def test_course_loading(self):
        '''Tests if a course file loads correctly'''
        print("\033[1m-> common-courses: course loading\033[0m")
        c = self.course_factory.get_course('test')
        assert c.get_id() == 'test'
        assert c._content['accessible'] == True
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 1'

        c = self.course_factory.get_course('test2')
        assert c.get_id() == 'test2'
        assert c._content['accessible'] == '1970-01-01/2033-01-01'
        assert c._content['admins'] == ['testadmin1']
        assert c._content['name'] == 'Unit test 2'

        # This one is in JSON
        c = self.course_factory.get_course('test3')
        assert c.get_id() == 'test3'
        assert c._content['accessible'] == '1970-01-01/1970-12-31'
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 3'

    def test_invalid_coursename(self):
        try:
            self.course_factory.get_course('invalid/name')
        except:
            return
        assert False

    def test_unreadable_course(self):
        try:
            self.course_factory.get_course('invalid_course')
        except:
            return
        assert False

    def test_all_courses_loading(self):
        '''Tests if all courses are loaded by Course.get_all_courses()'''
        print("\033[1m-> common-courses: all courses loading\033[0m")
        c = self.course_factory.get_all_courses()
        assert 'test' in c
        assert 'test2' in c
        assert 'test3' in c

    def test_tasks_loading(self):
        '''Tests loading tasks from the get_tasks method'''
        print("\033[1m-> common-courses: course tasks loading\033[0m")
        c = self.course_factory.get_course('test')
        t = c.get_tasks()
        assert 'task1' in t
        assert 'task2' in t
        assert 'task3' in t
        assert 'task4' in t

    def test_tasks_loading_invalid(self):
        c = self.course_factory.get_course('test3')
        t = c.get_tasks()
        assert t == {}


class TestCourseWrite(object):
    """ Test the course update function """

    def setUp(self):
        register_base_env_types()
        self.dir_path = tempfile.mkdtemp()
        fs = LocalFSProvider(self.dir_path)
        self.course_factory, _ = create_factories(fs, task_dispensers, problem_types)

    def tearDown(self):
        shutil.rmtree(self.dir_path)

    def test_course_update(self):
        os.mkdir(os.path.join(self.dir_path, "test"))
        with open(os.path.join(self.dir_path, "test", "course.yaml"), "w") as f:
            f.write("""
name: "a"
admins: ["a"]
accessible: "1970-01-01/2033-01-01"
        """)
        assert self.course_factory.get_course_descriptor_content("test") == {"name": "a", "admins": ["a"], "accessible": "1970-01-01/2033-01-01"}
        self.course_factory.update_course_descriptor_content("test", {"name": "b", "admins": ["b"], "accessible": "1970-01-01/2030-01-01"})
        assert self.course_factory.get_course_descriptor_content("test") == {"name": "b", "admins": ["b"], "accessible": "1970-01-01/2030-01-01"}
