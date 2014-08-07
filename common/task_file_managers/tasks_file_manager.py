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
""" Task file managers """
from abc import ABCMeta, abstractmethod
import codecs
import os.path

from common.base import INGIniousConfiguration


class TaskFileManager(object):

    """ Manages a type of task file """
    __metaclass__ = ABCMeta

    def __init__(self, courseid, taskid):
        self._courseid = courseid
        self._taskid = taskid

    def read(self):
        """ Read the file describing the task and returns a dict """
        return self._get_content(codecs.open(os.path.join(INGIniousConfiguration["tasks_directory"], self._courseid, self._taskid, "task." + self.get_ext()), "r", 'utf-8').read())

    @abstractmethod
    def _get_content(self, content):
        """ Read the file describing the task and returns a dict """
        pass

    @abstractmethod
    def get_ext(self):
        """ Returns the task file extension. Must be @classmethod! """
        pass

    def write(self, data):
        """ Write data to the task file """
        with codecs.open(os.path.join(INGIniousConfiguration["tasks_directory"], self._courseid, self._taskid, "task." + self.get_ext()), "w", 'utf-8') as task_desc_file:
            task_desc_file.write(self._generate_content(data))

    @abstractmethod
    def _generate_content(self, data):
        """ Generate data (that will be written to the file) """
        pass

    @classmethod
    def get_tasks(cls, courseid):
        """ Returns the list of all available tasks in a course """
        tasks = [
            task for task in os.listdir(
                os.path.join(
                    INGIniousConfiguration["tasks_directory"],
                    courseid)) if os.path.isdir(os.path.join(
                        INGIniousConfiguration["tasks_directory"],
                        courseid,
                        task)) and cls._task_file_exists(
                os.path.join(
                    INGIniousConfiguration["tasks_directory"],
                    courseid,
                    task))]
        return tasks

    @classmethod
    def _task_file_exists(cls, directory):
        """ Returns true if a task file exists in this directory """
        for filename in ["task.{}".format(subclass.get_ext()) for subclass in TaskFileManager.__subclasses__()]:
            if os.path.isfile(os.path.join(directory, filename)):
                return True
        return False

    @classmethod
    def get_manager(cls, courseid, taskid):
        """ Returns the appropriate task file manager for this task """
        for subclass in TaskFileManager.__subclasses__():
            if os.path.isfile(os.path.join(INGIniousConfiguration["tasks_directory"], courseid, taskid, "task.{}".format(subclass.get_ext()))):
                return subclass(courseid, taskid)
        return None

    @classmethod
    def delete_all_possible_task_files(cls, courseid, taskid):
        """ Deletes all possibles task files in directory, to allow to change the format """
        for subclass in TaskFileManager.__subclasses__():
            try:
                os.remove(os.path.join(INGIniousConfiguration["tasks_directory"], courseid, taskid, "task.{}".format(subclass.get_ext())))
            except:
                pass

    @classmethod
    def get_available_file_managers(cls):
        """ Get a dict with ext:class pairs """
        return {f.get_ext(): f for f in TaskFileManager.__subclasses__()}