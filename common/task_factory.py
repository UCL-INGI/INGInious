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
""" Factory for loading tasks from disk """

from common.tasks import Task
from common.task_file_managers.manage import get_readable_tasks, get_available_task_file_managers
from common.base import id_checker
import os
from common.exceptions import InvalidNameException, TaskNotFoundException, TaskUnreadableException

class TaskFactory(object):
    """ Load courses from disk """

    def __init__(self, tasks_directory, task_class=Task):
        self._tasks_directory = tasks_directory
        self._task_class = task_class
        self._cache = {}

    def get_task(self, course, taskid):
        """
        :param course: a Course object
        :param taskid: the task id of the task
        :raise InvalidNameException, TaskNotFoundException, TaskUnreadableException
        :return: an object representing the task, of the type given in the constructor
        """
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)
        if self._cache_update_needed(course, taskid):
            self._update_cache(course, taskid)
        return self._cache[(course.get_id(), taskid)][0]

    def get_all_tasks(self, course):
        """
        :return: a table containing taskid=>Task pairs
        """
        tasks = get_readable_tasks(course.get_id())
        output = {}
        for task in tasks:
            try:
                output[task] = self.get_task(course, task)
            except:
                pass
        return output

    def _get_task_descriptor_info(self, courseid, taskid):
        """
        :param courseid: the course id of the course
        :param taskid: the task id of the task
        :raise InvalidNameException, TaskNotFoundException
        :return: a tuple, containing:
            (the path to the descriptor of the task,
             extension of the descriptor,
             task file manager for the descriptor)
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)
        base_file = os.path.join(self._tasks_directory, courseid, taskid, "task")

        for ext, task_file_manager in get_available_task_file_managers().iteritems():
            if os.path.isfile(base_file + "." + ext):
                return (base_file + "." + ext, ext, task_file_manager)

        raise TaskNotFoundException()

    def _cache_update_needed(self, course, taskid):
        """
        :param course: a Course object
        :param taskid: a (valid) task id
        :raise InvalidNameException, TaskNotFoundException
        :return: True if an update of the cache is needed, False else
        """
        if (course.get_id(), taskid) not in self._cache:
            return True
        try:
            last_update = os.stat(self._get_task_descriptor_info(course.get_id(), taskid)[0]).st_mtime
        except:
            raise TaskNotFoundException()

        if self._cache[(course.get_id(), taskid)][1] < last_update:
            return True

    def _update_cache(self, course, taskid):
        """
        Updates the cache
        :param course: a Course object
        :param taskid: a (valid) task id
        :raise InvalidNameException, TaskNotFoundException, TaskUnreadableException
        """
        path_to_descriptor, descriptor_ext, descriptor_manager = self._get_task_descriptor_info(course.get_id(), taskid)
        try:
            task_content = descriptor_manager(course.get_id(), taskid).read()
        except Exception as e:
            raise TaskUnreadableException(str(e))
        self._cache[(course.get_id(), taskid)] = (self._task_class(course, taskid, task_content), os.stat(path_to_descriptor).st_mtime)