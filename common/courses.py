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
import json
import os
import os.path

from common.base import INGIniousConfiguration, id_checker
from common.task_file_managers.tasks_file_manager import TaskFileManager
import common.tasks


class Course(object):

    """ Represents a course """

    _task_class = common.tasks.Task

    @classmethod
    def get_course_descriptor_path(cls, courseid):
        """Returns the path to the json that describes the course 'courseid'"""
        if not id_checker(courseid):
            raise Exception("Course with invalid name: " + courseid)
        return os.path.join(INGIniousConfiguration["tasks_directory"], courseid, "course.json")

    @classmethod
    def get_all_courses(cls):
        """Returns a table containing courseid=>Course pairs."""
        files = [os.path.splitext(f)[0] for f in os.listdir(INGIniousConfiguration["tasks_directory"]) if os.path.isfile(os.path.join(INGIniousConfiguration["tasks_directory"], f, "course.json"))]
        output = {}
        for course in files:
            try:
                output[course] = cls(course)
            except:  # todo log the error
                pass
        return output

    def __init__(self, courseid):
        """Constructor. courseid is the name of the the folder containing the file course.json"""

        self._content = json.load(open(self.get_course_descriptor_path(courseid), "r"))
        self._id = courseid
        self._tasks_cache = None

    def get_original_content(self):
        """ Return the original content of the json file describing this course """
        return self._content

    def get_task(self, taskid):
        """ Return the class with name taskid """
        return self._task_class(self, taskid)

    def get_id(self):
        """ Return the _id of this course """
        return self._id

    def get_course_tasks_directory(self):
        """Return the complete path to the tasks directory of the course"""
        return os.path.join(INGIniousConfiguration["tasks_directory"], self._id)

    def get_tasks(self):
        """Get all tasks in this course"""
        if self._tasks_cache is None:
            tasks = TaskFileManager.get_tasks(self.get_id())
            output = {}
            for task in tasks:
                try:
                    output[task] = self.get_task(task)
                except:
                    pass
            self._tasks_cache = output
        return self._tasks_cache
