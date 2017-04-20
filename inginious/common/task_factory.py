# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Factory for loading tasks from disk """

import os
import codecs
import shutil

from inginious.common.log import get_course_logger
from inginious.common.tasks import Task
from inginious.common.base import id_checker
from inginious.common.task_file_readers.yaml_reader import TaskYAMLFileReader
from inginious.common.exceptions import InvalidNameException, TaskNotFoundException, TaskUnreadableException, TaskReaderNotFoundException

class TaskFactory(object):
    """ Load courses from disk """

    def __init__(self, tasks_directory, hook_manager, task_class=Task):
        self._tasks_directory = tasks_directory
        self._task_class = task_class
        self._hook_manager = hook_manager
        self._cache = {}
        self._task_file_managers = {}
        self.add_custom_task_file_manager(TaskYAMLFileReader())

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

    def get_task_descriptor_content(self, courseid, taskid):
        """
        :param courseid: the course id of the course
        :param taskid: the task id of the task
        :raise InvalidNameException, TaskNotFoundException, TaskUnreadableException
        :return: the content of the task descriptor, as a dict
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)
        path_to_descriptor, _, descriptor_manager = self._get_task_descriptor_info(courseid, taskid)
        try:
            with codecs.open(path_to_descriptor, 'r', 'utf-8') as fd:
                task_content = descriptor_manager.load(fd.read())
        except Exception as e:
            raise TaskUnreadableException(str(e))
        return task_content

    def get_task_descriptor_extension(self, courseid, taskid):
        """
            :param courseid: the course id of the course
            :param taskid: the task id of the task
            :raise InvalidNameException, TaskNotFoundException
            :return: the current extension of the task descriptor
            """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)
        _, descriptor_ext, _2 = self._get_task_descriptor_info(courseid, taskid)
        return descriptor_ext

    def get_directory_path(self, courseid, taskid):
        """
        :param courseid: the course id of the course
        :param taskid: the task id of the task
        :raise InvalidNameException
        :return: The path to the directory that contains the files related to the task
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)
        return os.path.join(self._tasks_directory, courseid, taskid)

    def update_task_descriptor_content(self, courseid, taskid, content, force_extension=None):
        """
        Update the task descriptor with the dict in content
        :param course: the course id of the course
        :param taskid: the task id of the task
        :param content: the content to put in the task file
        :param force_extension: If None, save it the same format. Else, save with the given extension
        :raise InvalidNameException, TaskNotFoundException, TaskUnreadableException
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)

        if force_extension is None:
            path_to_descriptor, _, descriptor_manager = self._get_task_descriptor_info(courseid, taskid)
        elif force_extension in self.get_available_task_file_extensions():
            path_to_descriptor = os.path.join(self._tasks_directory, courseid, taskid, "task." + force_extension)
            descriptor_manager = self._task_file_managers[force_extension]
        else:
            raise TaskReaderNotFoundException()

        try:
            with codecs.open(path_to_descriptor, 'w', 'utf-8') as fd:
                fd.write(descriptor_manager.dump(content))
        except:
            raise TaskNotFoundException()

    def get_readable_tasks(self, course):
        """ Returns the list of all available tasks in a course """
        tasks = [
            task for task in os.listdir(os.path.join(self._tasks_directory, course.get_id()))
            if os.path.isdir(os.path.join(self._tasks_directory, course.get_id(), task))
            and self._task_file_exists(os.path.join(self._tasks_directory, course.get_id(), task))]
        return tasks

    def _task_file_exists(self, directory):
        """ Returns true if a task file exists in this directory """
        for filename in ["task.{}".format(ext) for ext in self.get_available_task_file_extensions()]:
            if os.path.isfile(os.path.join(directory, filename)):
                return True
        return False

    def delete_all_possible_task_files(self, courseid, taskid):
        """ Deletes all possibles task files in directory, to allow to change the format """
        for ext in self.get_available_task_file_extensions():
            try:
                os.remove(os.path.join(self._tasks_directory, courseid, taskid, "task.{}".format(ext)))
            except:
                pass

    def get_all_tasks(self, course):
        """
        :return: a table containing taskid=>Task pairs
        """
        tasks = self.get_readable_tasks(course)
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

        for ext, task_file_manager in self._task_file_managers.items():
            if os.path.isfile(base_file + "." + ext):
                return base_file + "." + ext, ext, task_file_manager

        raise TaskNotFoundException()

    def add_custom_task_file_manager(self, task_file_manager):
        """ Add a custom task file manager """
        self._task_file_managers[task_file_manager.get_ext()] = task_file_manager

    def get_available_task_file_extensions(self):
        """ Get a list of all the extensions possible for task descriptors """
        return list(self._task_file_managers.keys())

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
        path_to_descriptor, _, descriptor_reader = self._get_task_descriptor_info(course.get_id(), taskid)
        try:
            with codecs.open(path_to_descriptor, 'r', 'utf-8') as fd:
                task_content = descriptor_reader.load(fd.read())
        except Exception as e:
            raise TaskUnreadableException(str(e))

        self._cache[(course.get_id(), taskid)] = (
            self._task_class(course, taskid, task_content, self.get_directory_path(course.get_id(), taskid), self._hook_manager),
            os.stat(path_to_descriptor).st_mtime
        )

    def update_cache_for_course(self, courseid):
        """
        Clean/update the cache of all the tasks for a given course (id)
        :param courseid:
        """
        to_drop = []
        for (cid, tid) in self._cache:
            if cid == courseid:
                to_drop.append(tid)
        for tid in to_drop:
            del self._cache[(courseid, tid)]

    def delete_task(self, courseid, taskid):
        """
        :param courseid: the course id of the course
        :param taskid: the task id of the task
        :raise InvalidNameException or CourseNotFoundException
        Erase the content of the task folder
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)

        task_directory = os.path.join(self._tasks_directory, courseid, taskid)

        if not os.path.exists(task_directory):
            raise TaskNotFoundException()

        shutil.rmtree(task_directory)

        get_course_logger(courseid).info("Task %s erased from the factory.", taskid)
