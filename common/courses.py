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
""" Contains the class Course and utility functions """
import os.path

from common.base import get_tasks_directory, id_checker, load_json_or_yaml, write_json_or_yaml
from common.task_file_managers.manage import get_readable_tasks
import common.tasks


class Course(object):

    """ Represents a course """

    _task_class = common.tasks.Task

    @classmethod
    def _get_course_descriptor_path(cls, courseid):
        """Returns the path to the file that describes the course 'courseid'"""
        if not id_checker(courseid):
            raise Exception("Course with invalid name: " + courseid)
        base_file = os.path.join(get_tasks_directory(), courseid, "course")
        if os.path.isfile(base_file + ".yaml"):
            return base_file + ".yaml"
        else:
            return base_file + ".json"

    @classmethod
    def get_course_descriptor_content(cls, courseid):
        """ Returns the content of the dict that describes the course """
        return load_json_or_yaml(cls._get_course_descriptor_path(courseid))

    @classmethod
    def update_course_descriptor_content(cls, courseid, content):
        """ Updates the content of the dict that describes the course """
        return write_json_or_yaml(cls._get_course_descriptor_path(courseid), content)

    @classmethod
    def get_all_courses(cls):
        """Returns a table containing courseid=>Course pairs."""
        files = [os.path.splitext(f)[0] for f in os.listdir(get_tasks_directory()) if
                 os.path.isfile(os.path.join(get_tasks_directory(), f, "course.yaml")) or
                 os.path.isfile(os.path.join(get_tasks_directory(), f, "course.json"))]
        output = {}
        for course in files:
            try:
                output[course] = cls(course)
            except Exception as e:  # todo log the error
                print e
        return output

    def __init__(self, courseid):
        """Constructor. courseid is the name of the the folder containing the file course.json"""
        self._content = self.get_course_descriptor_content(courseid)
        self._id = courseid
        self._tasks_cache = None

    def get_task(self, taskid):
        """ Return the class with name taskid """
        return self._task_class(self, taskid)

    def get_id(self):
        """ Return the _id of this course """
        return self._id

    def get_course_tasks_directory(self):
        """Return the complete path to the tasks directory of the course"""
        return os.path.join(get_tasks_directory(), self._id)

    def get_tasks(self):
        """Get all tasks in this course"""
        if self._tasks_cache is None:
            tasks = get_readable_tasks(self.get_id())
            output = {}
            for task in tasks:
                try:
                    output[task] = self.get_task(task)
                except:
                    pass
            self._tasks_cache = output
        return self._tasks_cache
