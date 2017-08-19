# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Factory for loading courses from disk """
from inginious.common.filesystems.provider import FileSystemProvider
from inginious.common.log import get_course_logger
from inginious.common.courses import Course
from inginious.common.base import id_checker, get_json_or_yaml, loads_json_or_yaml
from inginious.common.task_factory import TaskFactory
from inginious.common.tasks import Task
from inginious.common.hook_manager import HookManager
from inginious.common.exceptions import InvalidNameException, CourseNotFoundException, CourseUnreadableException, CourseAlreadyExistsException


class CourseFactory(object):
    """ Load courses from disk """

    def __init__(self, filesystem: FileSystemProvider, task_factory, hook_manager, course_class=Course):
        self._filesystem = filesystem
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
        path = self._get_course_descriptor_path(courseid)
        return loads_json_or_yaml(path, self._filesystem.get(path).decode("utf-8"))

    def update_course_descriptor_content(self, courseid, content):
        """
        Updates the content of the dict that describes the course
        :param courseid: the course id of the course
        :param content: the new dict that replaces the old content
        :raise InvalidNameException, CourseNotFoundException
        """
        path = self._get_course_descriptor_path(courseid)
        self._filesystem.put(path, get_json_or_yaml(path, content))

    def get_course_fs(self, courseid):
        """
        :param courseid: 
        :return: a FileSystemProvider pointing to the directory of the course 
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        return self._filesystem.from_subfolder(courseid)

    def get_all_courses(self):
        """
        :return: a table containing courseid=>Course pairs
        """
        course_ids = [f[0:len(f)-1] for f in self._filesystem.list(folders=True, files=False, recursive=False)]  # remove trailing "/"
        output = {}
        for courseid in course_ids:
            try:
                output[courseid] = self.get_course(courseid)
            except Exception:
                get_course_logger(courseid).warning("Cannot open course", exc_info=True)
        return output

    def _get_course_descriptor_path(self, courseid):
        """
        :param courseid: the course id of the course
        :raise InvalidNameException, CourseNotFoundException
        :return: the path to the descriptor of the course
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)
        course_fs = self.get_course_fs(courseid)
        if course_fs.exists("course.yaml"):
            return courseid+"/course.yaml"
        if course_fs.exists("course.json"):
            return courseid+"/course.json"
        raise CourseNotFoundException()

    def create_course(self, courseid, init_content):
        """
        :param courseid: the course id of the course
        :param init_content: initial descriptor content
        :raise InvalidNameException or CourseAlreadyExistsException
        Create a new course folder and set initial descriptor content, folder can already exist
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)

        course_fs = self.get_course_fs(courseid)
        course_fs.ensure_exists()

        if course_fs.exists("course.yaml") or course_fs.exists("course.json"):
            raise CourseAlreadyExistsException("Course with id " + courseid + " already exists.")
        else:
            course_fs.put("course.yaml", get_json_or_yaml("course.yaml", init_content))

        get_course_logger(courseid).info("Course %s created in the factory.", courseid)

    def delete_course(self, courseid):
        """
        :param courseid: the course id of the course
        :raise InvalidNameException or CourseNotFoundException
        Erase the content of the course folder
        """
        if not id_checker(courseid):
            raise InvalidNameException("Course with invalid name: " + courseid)

        course_fs = self.get_course_fs(courseid)

        if not course_fs.exists():
            raise CourseNotFoundException()

        course_fs.delete()

        get_course_logger(courseid).info("Course %s erased from the factory.", courseid)

    def _cache_update_needed(self, courseid):
        """
        :param courseid: the (valid) course id of the course
        :raise InvalidNameException, CourseNotFoundException
        :return: True if an update of the cache is needed, False else
        """
        if courseid not in self._cache:
            return True

        try:
            last_update = self._filesystem.get_last_modification_time(self._get_course_descriptor_path(courseid))
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
            course_descriptor = loads_json_or_yaml(path_to_descriptor, self._filesystem.get(path_to_descriptor).decode("utf8"))
            last_modification = self._filesystem.get_last_modification_time(path_to_descriptor)
        except Exception as e:
            raise CourseUnreadableException(str(e))
        self._cache[courseid] = (self._course_class(courseid, course_descriptor, self._task_factory, self._hook_manager), last_modification)
        self._task_factory.update_cache_for_course(courseid)


def create_factories(fs_provider, hook_manager=None, course_class=Course, task_class=Task):
    """
    Shorthand for creating Factories
    :param fs_provider: A FileSystemProvider leading to the courses
    :param hook_manager: an Hook Manager instance. If None, a new Hook Manager is created
    :param course_class:
    :param task_class:
    :return: a tuple with two objects: the first being of type CourseFactory, the second of type TaskFactory
    """
    if hook_manager is None:
        hook_manager = HookManager()

    task_factory = TaskFactory(fs_provider, hook_manager, task_class)
    return CourseFactory(fs_provider, task_factory, hook_manager, course_class), task_factory
