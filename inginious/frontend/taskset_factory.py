# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Factory for loading tasksets from disk """
import logging

from inginious.common.filesystems import FileSystemProvider
from inginious.frontend.log import get_taskset_logger
from inginious.common.base import id_checker, get_json_or_yaml, loads_json_or_yaml
from inginious.frontend.plugin_manager import PluginManager
from inginious.common.exceptions import InvalidNameException
from inginious.frontend.exceptions import TasksetNotFoundException, TasksetUnreadableException, TasksetAlreadyExistsException

from inginious.frontend.tasksets import Taskset
from inginious.frontend.task_factory import TaskFactory
from inginious.frontend.course_factory import CourseFactory


class TasksetFactory(object):
    """ Load tasksets from disk """
    _logger = logging.getLogger("inginious.taskset_factory")

    def __init__(self, filesystem: FileSystemProvider, task_factory, task_dispensers, database):
        self._filesystem = filesystem
        self._task_factory = task_factory
        self._task_dispensers = task_dispensers
        self._database = database
        self._cache = {}

    def add_task_dispenser(self, task_dispenser):
        """
        :param task_dispenser: TaskDispenser class
        """
        self._task_dispensers.update({task_dispenser.get_id(): task_dispenser})

    def get_task_dispensers(self):
        """
        Returns the supported task dispensers by this taskset factory
        """
        return self._task_dispensers

    def get_taskset(self, tasksetid):
        """
        :param tasksetid: the taskset id id of the taskset
        :raise: InvalidNameException, CourseNotFoundException, CourseUnreadableException
        :return: an object representing the taskset, of the type given in the constructor
        """
        if not id_checker(tasksetid):
            raise InvalidNameException("Taskset with invalid name: " + tasksetid)
        if self._cache_update_needed(tasksetid):
            self._update_cache(tasksetid)

        return self._cache[tasksetid][0]

    def get_task_factory(self):
        """
        :return: the associated task factory
        """
        return self._task_factory

    def get_taskset_descriptor_content(self, tasksetid):
        """
        :param tasksetid: the taskset id of the taskset
        :raise: InvalidNameException, TasksetNotFoundException, TasksetUnreadableException
        :return: the content of the dict that describes the task set
        """
        path = self._get_taskset_descriptor_path(tasksetid)
        return loads_json_or_yaml(path, self._filesystem.get(path).decode("utf-8"))

    def update_taskset_descriptor_content(self, tasksetid, content):
        """
        Updates the content of the dict that describes the task set
        :param tasksetid: the taskset id of the task set
        :param content: the new dict that replaces the old content
        :raise InvalidNameException, TasksetNotFoundException
        """
        path = self._get_taskset_descriptor_path(tasksetid, update=True)
        self._filesystem.put(path, get_json_or_yaml(path, content))

    def update_taskset_descriptor_element(self, tasksetid, key, value):
        """
        Updates the value for the key in the dict that describes the task set
        :param tasksetid: the taskset id of the task set
        :param key: the element to change in the dict
        :param value: the new value that replaces the old one
        :raise InvalidNameException, TasksetNotFoundException
        """
        taskset_structure = self.get_taskset_descriptor_content(tasksetid)
        taskset_structure[key] = value
        self.update_taskset_descriptor_content(tasksetid, taskset_structure)

    def get_fs(self):
        """
        :return: a FileSystemProvider pointing to the task directory
        """
        return self._filesystem

    def get_taskset_fs(self, tasksetid):
        """
        :param tasksetid: the taskset id of the task set
        :return: a FileSystemProvider pointing to the directory of the task set
        """
        if not id_checker(tasksetid):
            raise InvalidNameException("Taskset with invalid name: " + tasksetid)
        return self._filesystem.from_subfolder(tasksetid)

    def get_all_tasksets(self):
        """
        :return: a table containing tasksetid => Taskset pairs
        """
        taskset_ids = [f[0:len(f)-1] for f in self._filesystem.list(folders=True, files=False, recursive=False)]  # remove trailing "/"
        output = {}
        for tasksetid in taskset_ids:
            try:
                output[tasksetid] = self.get_taskset(tasksetid)
            except Exception:
                get_taskset_logger(tasksetid).warning("Cannot open taskset", exc_info=True)
        return output

    def _get_taskset_descriptor_path(self, tasksetid, update=False):
        """
        :param tasksetid: the taskset id of the task set
        :raise InvalidNameException, TasksetNotFoundException
        :return: the path to the descriptor of the task set
        """
        if not id_checker(tasksetid):
            raise InvalidNameException("Taskset with invalid name: " + tasksetid)
        taskset_fs = self.get_taskset_fs(tasksetid)
        if taskset_fs.exists("taskset.yaml") or update:
            return tasksetid + "/taskset.yaml"
        if taskset_fs.exists("course.yaml"):
            return tasksetid + "/course.yaml"
        if taskset_fs.exists("course.json"):
            return tasksetid + "/course.json"
        raise TasksetNotFoundException()

    def create_taskset(self, tasksetid, init_content):
        """
        Create a new taskset folder and set initial descriptor content, folder can already exist
        :param tasksetid: the taskset id of the taskset
        :param init_content: initial descriptor content
        :raise: InvalidNameException or CourseAlreadyExistsException
        """
        if not id_checker(tasksetid):
            raise InvalidNameException("Taskset with invalid name: " + tasksetid)

        taskset_fs = self.get_taskset_fs(tasksetid)
        taskset_fs.ensure_exists()

        if taskset_fs.exists("taskset.yaml"):
            raise TasksetAlreadyExistsException("Taskset with id " + tasksetid + " already exists.")
        else:
            taskset_fs.put("taskset.yaml", get_json_or_yaml("taskset.yaml", init_content))

        get_taskset_logger(tasksetid).info("Taskset %s created in the factory.", tasksetid)

    def delete_taskset(self, tasksetid):
        """
        Erase the content of the taskset folder
        :param tasksetid: the taskset id of the taskset
        :raise: InvalidNameException or CourseNotFoundException
        """
        if not id_checker(tasksetid):
            raise InvalidNameException("Taskset with invalid name: " + tasksetid)

        taskset_fs = self.get_taskset_fs(tasksetid)

        if not taskset_fs.exists():
            raise TasksetNotFoundException()

        taskset_fs.delete()

        get_taskset_logger(tasksetid).info("Taskset %s erased from the factory.", tasksetid)

    def _cache_update_needed(self, tasksetid):
        """
        :param tasksetid: the (valid) taskset id of the taskset
        :raise InvalidNameException, CourseNotFoundException
        :return: True if an update of the cache is needed, False else
        """
        if tasksetid not in self._cache:
            return True

        try:
            descriptor_name = self._get_taskset_descriptor_path(tasksetid)
            last_update = {descriptor_name: self._filesystem.get_last_modification_time(descriptor_name)}
            translations_fs = self._filesystem.from_subfolder("$i18n")
            if translations_fs.exists():
                for f in translations_fs.list(folders=False, files=True, recursive=False):
                    lang = f[0:len(f) - 3]
                    if translations_fs.exists(lang + ".mo"):
                        last_update["$i18n/" + lang + ".mo"] = translations_fs.get_last_modification_time(lang + ".mo")
        except:
            raise TasksetNotFoundException()

        last_modif = self._cache[tasksetid][1]
        for filename, mftime in last_update.items():
            if filename not in last_modif or last_modif[filename] < mftime:
                return True

        return False

    def _update_cache(self, tasksetid):
        """
        Updates the cache
        :param tasksetid: the (valid) taskset id of the taskset
        :raise InvalidNameException, CourseNotFoundException, CourseUnreadableException
        """
        self._logger.info("Caching taskset {}".format(tasksetid))
        path_to_descriptor = self._get_taskset_descriptor_path(tasksetid)
        try:
            taskset_descriptor = loads_json_or_yaml(path_to_descriptor, self._filesystem.get(path_to_descriptor).decode("utf8"))
        except Exception as e:
            raise TasksetUnreadableException(str(e))

        last_modif = {path_to_descriptor: self._filesystem.get_last_modification_time(path_to_descriptor)}
        translations_fs = self._filesystem.from_subfolder("$i18n")
        if translations_fs.exists():
            for f in translations_fs.list(folders=False, files=True, recursive=False):
                lang = f[0:len(f) - 3]
                if translations_fs.exists(lang + ".mo"):
                    last_modif["$i18n/" + lang + ".mo"] = translations_fs.get_last_modification_time(lang + ".mo")

        self._cache[tasksetid] = (
            Taskset(tasksetid, taskset_descriptor, self.get_taskset_fs(tasksetid), self._task_factory,
                    self._task_dispensers, self._database, "course" in path_to_descriptor),
            last_modif
        )

        self._task_factory.update_cache_for_taskset(tasksetid)


def create_factories(fs_provider, task_dispensers, task_problem_types, plugin_manager=None, database=None):
    """
    Shorthand for creating Factories
    :param fs_provider: A FileSystemProvider leading to the tasksets
    :param plugin_manager: a Plugin Manager instance. If None, a new Hook Manager is created
    :param task_class:
    :return: a tuple with two objects: the first being of type CourseFactory, the second of type TaskFactory
    """
    if plugin_manager is None:
        plugin_manager = PluginManager()

    task_factory = TaskFactory(fs_provider, plugin_manager, task_problem_types)
    taskset_factory = TasksetFactory(fs_provider, task_factory, task_dispensers, database)
    course_factory = CourseFactory(taskset_factory, task_factory, plugin_manager, database) if database is not None else None

    return taskset_factory, course_factory, task_factory
