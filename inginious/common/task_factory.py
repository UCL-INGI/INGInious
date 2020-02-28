# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Factory for loading tasks from disk """
from typing import TYPE_CHECKING, Type, Dict, Tuple, List, Any, Optional
from os.path import splitext

from inginious.common.filesystems.provider import FileSystemProvider
from inginious.common.log import get_course_logger
from inginious.common.tasks import Task
from inginious.common.base import id_checker
from inginious.common.task_file_readers.yaml_reader import TaskYAMLFileReader
from inginious.common.exceptions import InvalidNameException, TaskNotFoundException, TaskUnreadableException, TaskReaderNotFoundException

if TYPE_CHECKING:
    from inginious.common.courses import Course
    from inginious.common.hook_manager import HookManager
    from inginious.common.tasks_problems import Problem
    from inginious.common.task_file_readers.abstract_reader import AbstractTaskFileReader


class TaskFactory(object):
    """ Load courses from disk """

    def __init__(self, filesystem: FileSystemProvider, hook_manager: 'HookManager', task_problem_types: Dict[str, Type['Problem']], task_class: Type['Task'] = Task):
        self._filesystem = filesystem
        self._task_class = task_class
        self._hook_manager = hook_manager
        self._cache: Dict[Tuple[str, str], Tuple[Task, Dict[str, float]]] = {}
        self._task_file_managers: Dict[str, 'AbstractTaskFileReader'] = {}
        self._task_problem_types = task_problem_types
        self.add_custom_task_file_manager(TaskYAMLFileReader())

    def add_problem_type(self, problem_type: Type['Problem']):
        """
        :param problem_type: Problem class
        """
        self._task_problem_types.update({problem_type.get_type(): problem_type})

    def get_task(self, course: 'Course', taskid: str) -> 'Task':
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

    def get_task_descriptor_content(self, courseid: str, taskid: str) -> Dict[Any, Any]:
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

        descriptor_path, descriptor_manager = self._get_task_descriptor_info(courseid, taskid)
        try:
            task_content = descriptor_manager.load(self.get_task_fs(courseid, taskid).get(descriptor_path))
        except Exception as e:
            raise TaskUnreadableException(str(e))
        return task_content

    def get_task_descriptor_extension(self, courseid: str, taskid: str) -> str:
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
        descriptor_path = self._get_task_descriptor_info(courseid, taskid)[0]
        return splitext(descriptor_path)[1]

    def get_task_fs(self, courseid: str, taskid: str) -> FileSystemProvider:
        """
        :param courseid: the course id of the course
        :param taskid: the task id of the task
        :raise InvalidNameException
        :return: A FileSystemProvider to the folder containing the task files
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)
        return self._filesystem.from_subfolder(courseid).from_subfolder(taskid)

    def update_task_descriptor_content(self, courseid: str, taskid: str, content: Dict[Any, Any], force_extension: Optional[str] = None):
        """
        Update the task descriptor with the dict in content
        :param courseid: the course id of the course
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
            path_to_descriptor, descriptor_manager = self._get_task_descriptor_info(courseid, taskid)
        elif force_extension in self.get_available_task_file_extensions():
            path_to_descriptor = "task." + force_extension
            descriptor_manager = self._task_file_managers[force_extension]
        else:
            raise TaskReaderNotFoundException()

        try:
            self.get_task_fs(courseid, taskid).put(path_to_descriptor, descriptor_manager.dump(content))
        except:
            raise TaskNotFoundException()

    def get_readable_tasks(self, course: 'Course') -> List[str]:
        """ Returns the list of all available tasks in a course """
        course_fs = self._filesystem.from_subfolder(course.get_id())
        tasks = [
            task[0:len(task)-1]  # remove trailing /
            for task in course_fs.list(folders=True, files=False, recursive=False)
            if self._task_file_exists(course_fs.from_subfolder(task))]
        return tasks

    def _task_file_exists(self, task_fs: FileSystemProvider) -> bool:
        """ Returns true if a task file exists in this directory """
        for filename in ["task.{}".format(ext) for ext in self.get_available_task_file_extensions()]:
            if task_fs.exists(filename):
                return True
        return False

    def delete_all_possible_task_files(self, courseid: str, taskid: str):
        """ Deletes all possibles task files in directory, to allow to change the format """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)
        task_fs = self.get_task_fs(courseid, taskid)
        for ext in self.get_available_task_file_extensions():
            try:
                task_fs.delete("task."+ext)
            except:
                pass

    def get_all_tasks(self, course: 'Course') -> Dict[str, Task]:
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

    def _get_task_descriptor_info(self, courseid: str, taskid: str) -> Tuple[str, 'AbstractTaskFileReader']:
        """
        :param courseid: the course id of the course
        :param taskid: the task id of the task
        :raise InvalidNameException, TaskNotFoundException
        :return: a tuple, containing:
            (descriptor filename,
             task file manager for the descriptor)
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)

        task_fs = self.get_task_fs(courseid, taskid)
        for ext, task_file_manager in self._task_file_managers.items():
            if task_fs.exists("task."+ext):
                return "task." + ext, task_file_manager

        raise TaskNotFoundException()

    def add_custom_task_file_manager(self, task_file_manager: 'AbstractTaskFileReader'):
        """ Add a custom task file manager """
        self._task_file_managers[task_file_manager.get_ext()] = task_file_manager

    def get_available_task_file_extensions(self) -> List[str]:
        """ Get a list of all the extensions possible for task descriptors """
        return list(self._task_file_managers.keys())

    def _cache_update_needed(self, course: 'Course', taskid: str) -> bool:
        """
        :param course: a Course object
        :param taskid: a (valid) task id
        :raise InvalidNameException, TaskNotFoundException
        :return: True if an update of the cache is needed, False else
        """
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)

        task_fs = self.get_task_fs(course.get_id(), taskid)

        if (course.get_id(), taskid) not in self._cache:
            return True

        try:
            last_update, _, _ = self._get_last_updates(course, taskid, task_fs, False)
        except:
            raise TaskNotFoundException()

        last_modif = self._cache[(course.get_id(), taskid)][1]
        for filename, mftime in last_update.items():
            if filename not in last_modif or last_modif[filename] < mftime:
                return True

        return False

    def _get_last_updates(self, course: 'Course', taskid: str, task_fs: FileSystemProvider, need_content: bool = False) -> Tuple[Dict[str, float], FileSystemProvider, Optional[Dict[Any, Any]]]:
        descriptor_name, descriptor_reader = self._get_task_descriptor_info(course.get_id(), taskid)
        last_update = {descriptor_name: task_fs.get_last_modification_time(descriptor_name)}
        translations_fs = task_fs.from_subfolder("$i18n")

        if not translations_fs.exists():
            translations_fs = task_fs.from_subfolder("student").from_subfolder("$i18n")
        if not translations_fs.exists():
            translations_fs = course.get_fs().from_subfolder("$common").from_subfolder("$i18n")
        if not translations_fs.exists():
            translations_fs = course.get_fs().from_subfolder("$common").from_subfolder("student").from_subfolder(
                "$i18n")
        if not translations_fs.exists():
            translations_fs = course.get_fs().from_subfolder("$i18n")

        if translations_fs.exists():
            for f in translations_fs.list(folders=False, files=True, recursive=False):
                lang = f[0:len(f) - 3]
                if translations_fs.exists(lang + ".mo"):
                    last_update["$i18n/" + lang + ".mo"] = translations_fs.get_last_modification_time(lang + ".mo")

        if need_content:
            try:
                task_content = descriptor_reader.load(task_fs.get(descriptor_name))
            except Exception as e:
                raise TaskUnreadableException(str(e))
            return last_update, translations_fs, task_content
        else:
            return last_update, translations_fs, None

    def _update_cache(self, course: 'Course', taskid: str):
        """
        Updates the cache
        :param course: a Course object
        :param taskid: a (valid) task id
        :raise InvalidNameException, TaskNotFoundException, TaskUnreadableException
        """
        if not id_checker(taskid):
            raise InvalidNameException("Task with invalid name: " + taskid)

        task_fs = self.get_task_fs(course.get_id(), taskid)
        last_modif, translation_fs, task_content = self._get_last_updates(course, taskid, task_fs, True)

        self._cache[(course.get_id(), taskid)] = (
            self._task_class(course, taskid, task_content or {}, task_fs, translation_fs, self._hook_manager, self._task_problem_types),
            last_modif
        )

    def update_cache_for_course(self, courseid: str):
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

    def delete_task(self, courseid: str, taskid: str):
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

        task_fs = self.get_task_fs(courseid, taskid)

        if task_fs.exists():
            task_fs.delete()
            get_course_logger(courseid).info("Task %s erased from the factory.", taskid)

    def get_problem_types(self) -> Dict[str, Type['Problem']]:
        """
        Returns the supported problem types by this task factory
        """
        return self._task_problem_types
