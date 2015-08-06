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
""" Factory for loading courses from disk """

import os

from inginious.common.courses import Course
from inginious.common.base import id_checker, load_json_or_yaml, write_json_or_yaml
from inginious.common.task_factory import TaskFactory
from inginious.common.tasks import Task
from inginious.common.hook_manager import HookManager
from inginious.common.exceptions import InvalidNameException, CourseNotFoundException, CourseUnreadableException


class CourseFactory(object):
    """ Load courses from disk """

    def __init__(self, tasks_directory, task_factory, hook_manager, course_class=Course):
        self._tasks_directory = tasks_directory
        self._task_factory = task_factory
        self._hook_manager = hook_manager
        self._course_class = course_class
        self._cache = {}

    def get_course(self, courseid):
        """
        :param courseid: the course id of the course
        :raise InvalidNameException, CourseNotFoundException, CourseUnreadableException
        :return: an object representing the course, of the type given in the constructor
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if self._cache_update_needed(courseid):
            self._update_cache(courseid)
        return self._cache[courseid][0]

    def get_task(self, courseid, taskid):
        """
        Shorthand for CourseFactory.get_course(courseid).get_task(taskid)
        :param courseid: the course id of the course
        :param taskid: the task id of the task
        :raise InvalidNameException, CourseNotFoundException, CourseUnreadableException, TaskNotFoundException, TaskUnreadableException
        :return: an object representing the task, of the type given in the constructor
        """
        return self.get_course(courseid).get_task(taskid)

    def get_course_descriptor_content(self, courseid):
        """
        :param courseid: the course id of the course
        :raise InvalidNameException, CourseNotFoundException, CourseUnreadableException
        :return: the content of the dict that describes the course
        """
        return load_json_or_yaml(self._get_course_descriptor_path(courseid))

    def update_course_descriptor_content(self, courseid, content):
        """
        Updates the content of the dict that describes the course
        :param courseid: the course id of the course
        :param content: the new dict that replaces the old content
        :raise InvalidNameException, CourseNotFoundException
        """
        return write_json_or_yaml(self._get_course_descriptor_path(courseid), content)

    def get_all_courses(self):
        """
        :return: a table containing courseid=>Course pairs
        """
        course_ids = [os.path.splitext(f)[0] for f in os.listdir(self._tasks_directory) if
                      os.path.isfile(os.path.join(self._tasks_directory, f, "course.yaml")) or
                      os.path.isfile(os.path.join(self._tasks_directory, f, "course.json"))]
        output = {}
        for courseid in course_ids:
            try:
                output[courseid] = self.get_course(courseid)
            except Exception as e:  # todo log the error
                print e
        return output

    def _get_course_descriptor_path(self, courseid):
        """
        :param courseid: the course id of the course
        :raise InvalidNameException, CourseNotFoundException
        :return: the path to the descriptor of the course
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        base_file = os.path.join(self._tasks_directory, courseid, "course")
        if os.path.isfile(base_file + ".yaml"):
            return base_file + ".yaml"
        elif os.path.isfile(base_file + ".json"):
            return base_file + ".json"
        else:
            raise CourseNotFoundException()

    def _cache_update_needed(self, courseid):
        """
        :param courseid: the (valid) course id of the course
        :raise InvalidNameException, CourseNotFoundException
        :return: True if an update of the cache is needed, False else
        """
        if courseid not in self._cache:
            return True

        try:
            last_update = os.stat(self._get_course_descriptor_path(courseid)).st_mtime
        except:
            raise CourseNotFoundException()

        if self._cache[courseid][1] < last_update:
            return True

    def _update_cache(self, courseid):
        """
        Updates the cache
        :param courseid: the (valid) course id of the course
        :raise InvalidNameException, CourseNotFoundException, CourseUnreadableException
        """
        path_to_descriptor = self._get_course_descriptor_path(courseid)
        try:
            course_descriptor = load_json_or_yaml(path_to_descriptor)
        except Exception as e:
            raise CourseUnreadableException(str(e))
        self._cache[courseid] = (self._course_class(courseid, course_descriptor, self._task_factory), os.stat(path_to_descriptor).st_mtime)


def create_factories(task_directory, hook_manager=None, course_class=Course, task_class=Task):
    """
    Shorthand for creating Factories
    :param task_directory:
    :param hook_manager: an Hook Manager instance. If None, a new Hook Manager is created
    :param course_class:
    :param task_class:
    :return: a tuple with two objects: the first being of type CourseFactory, the second of type TaskFactory
    """
    if hook_manager is None:
        hook_manager = HookManager()

    task_factory = TaskFactory(task_directory, hook_manager, task_class)
    return CourseFactory(task_directory, task_factory, hook_manager, course_class), task_factory
