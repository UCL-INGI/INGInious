# pylint: disable=redefined-outer-name
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
from collections import OrderedDict

import pytest
import os
import tempfile
import shutil

from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.taskset_factory import create_factories
from inginious.common.tasks_problems import *
from inginious.frontend.task_dispensers.toc import TableOfContents
from inginious.frontend.environment_types import register_base_env_types
from inginious.frontend.task_dispensers.combinatory_test import CombinatoryTest

task_dispensers = {TableOfContents.get_id(): TableOfContents, CombinatoryTest.get_id(): CombinatoryTest}
problem_types = {"code": CodeProblem, "code_single_line": CodeSingleLineProblem, "file": FileProblem,
                 "multiple_choice": MultipleChoiceProblem, "match": MatchProblem}


@pytest.fixture()
def ressource(request):
    register_base_env_types()
    dir_path = tempfile.mkdtemp()
    fs = LocalFSProvider(os.path.join(os.path.dirname(__file__), 'tasks'))
    taskset_factory, course_factory, _ = create_factories(fs, task_dispensers, problem_types)
    yield (taskset_factory, dir_path)
    taskset_factory.update_taskset_descriptor_content("test", {"name": "Unit test 1", "admins": ["testadmin1","testadmin2"],
                                                             "public": True})
    shutil.rmtree(dir_path)


class TestCourse(object):

    def test_taskset_loading(self, ressource):
        """Tests if a taskset file loads correctly"""
        taskset_factory, temp_dir = ressource
        print("\033[1m-> common-tasksets: taskset loading\033[0m")
        c = taskset_factory.get_taskset('test')
        assert c.get_id() == 'test'
        assert c._content['public'] == True
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 1'

        c = taskset_factory.get_taskset('test2')
        assert c.get_id() == 'test2'
        assert c._content['public'] == False
        assert c._content['admins'] == ['testadmin1']
        assert c._content['name'] == 'Unit test 2'

        # This one is in JSON
        c = taskset_factory.get_taskset('test3')
        assert c.get_id() == 'test3'
        assert c._content['public'] == True
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 3'

    def test_invalid_tasksetname(self, ressource):
        try:
            taskset_factory, temp_dir = ressource
            taskset_factory.get_taskset('invalid/name')
        except:
            return
        assert False

    def test_unreadable_taskset(self, ressource):
        try:
            taskset_factory, temp_dir = ressource
            taskset_factory.get_taskset('invalid_taskset')
        except:
            return
        assert False

    def test_all_tasksets_loading(self, ressource):
        '''Tests if all tasksets are loaded by Course.get_all_tasksets()'''
        print("\033[1m-> common-tasksets: all tasksets loading\033[0m")
        taskset_factory, temp_dir = ressource
        c = taskset_factory.get_all_tasksets()
        assert 'test' in c
        assert 'test2' in c
        assert 'test3' in c

    def test_tasks_loading(self, ressource):
        '''Tests loading tasks from the get_tasks method'''
        print("\033[1m-> common-tasksets: taskset tasks loading\033[0m")
        taskset_factory, temp_dir = ressource
        c = taskset_factory.get_taskset('test')
        t = c.get_tasks()
        assert 'task1' in t
        assert 'task2' in t
        assert 'task3' in t
        assert 'task4' in t

    def test_tasks_loading_invalid(self, ressource):
        taskset_factory, temp_dir = ressource
        c = taskset_factory.get_taskset('test3')
        t = c.get_tasks()
        assert t == {}


class TestCourseWrite(object):
    """ Test the taskset update function """

    def test_taskset_update(self, ressource):
        taskset_factory, temp_dir = ressource
        os.mkdir(os.path.join(temp_dir, "test"))
        with open(os.path.join(temp_dir, "test", "taskset.yaml"), "w") as f:
            f.write("""
                name: "a"
                admins: ["a"]
                public: true
                        """)
        assert dict(taskset_factory.get_taskset_descriptor_content("test")) != {"name": "a", "admins": ["a"],
                                                                                    "public": True}
        taskset_factory.update_taskset_descriptor_content("test", {"name": "b", "admins": ["b"],
                                                                 "public": True})
        assert dict(taskset_factory.get_taskset_descriptor_content("test")) == {"name": "b", "admins": ["b"],
                                                                              "public": True}
