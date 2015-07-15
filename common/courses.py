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


class Course(object):
    """ Represents a course """

    def __init__(self, courseid, content_description, task_factory):
        """
        :param courseid: the course id
        :param content_description: a dict with all the infos of this course
        :param task_factory: a function with one argument, the task id, that returns a Task object
        """
        self._id = courseid
        self._content = content_description
        self._task_factory = task_factory

    def get_id(self):
        """ Return the _id of this course """
        return self._id

    def get_task(self, taskid):
        """ Returns a Task object """
        return self._task_factory.get_task(self, taskid)

    def get_tasks(self):
        """ Get all tasks in this course """
        return self._task_factory.get_all_tasks(self)
