# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Contains the class Course and utility functions """

import copy
import gettext
from typing import TYPE_CHECKING, List, Union, Dict


if TYPE_CHECKING:
    from inginious.common.filesystems.provider import FileSystemProvider
    from inginious.common.task_factory import Task, TaskFactory


class Course(object):
    """ Represents a course """

    def __init__(self, courseid: str, content_description, course_fs, task_factory: 'TaskFactory', hook_manager):
        """
        :param courseid: the course id
        :param content_description: a dict with all the infos of this course
        :param task_factory: a function with one argument, the task id, that returns a Task object
        """
        self._id = courseid
        self._content = content_description
        self._fs = course_fs
        self._task_factory = task_factory
        self._hook_manager = hook_manager

        self._translations: Dict[str, Union[gettext.GNUTranslations, gettext.NullTranslations]] = {}
        translations_fs = self._fs.from_subfolder("$i18n")
        if translations_fs.exists():
            for f in translations_fs.list(folders=False, files=True, recursive=False):
                lang = f[0:len(f) - 3]
                if translations_fs.exists(lang + ".mo"):
                    self._translations[lang] = gettext.GNUTranslations(translations_fs.get_fd(lang + ".mo"))
                else:
                    self._translations[lang] = gettext.NullTranslations()

    def get_translation_obj(self, language):
        return self._translations.get(language, gettext.NullTranslations())

    def gettext(self, language, *args, **kwargs):
        return self.get_translation_obj(language).gettext(*args, **kwargs)

    def get_id(self) -> str:
        """ Return the _id of this course """
        return self._id

    def get_fs(self) -> 'FileSystemProvider':
        """ Returns a FileSystemProvider which points to the folder of this course """
        return self._fs

    def get_task(self, taskid: str) -> 'Task':
        """ Returns a Task object """
        return self._task_factory.get_task(self, taskid)

    def get_tasks(self) -> Dict[str, 'Task']:
        """ Get all tasks in this course """
        return self._task_factory.get_all_tasks(self)

    def get_descriptor(self):
        """ Get (a copy) the description of the course """
        return copy.deepcopy(self._content)
