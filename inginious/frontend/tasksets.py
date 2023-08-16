# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A course class with some modification for users """

import copy
import gettext


class Taskset(object):
    """ A course with some modification for users """

    def __init__(self, tasksetid, content, course_fs, task_factory, legacy=False):
        self._id = tasksetid
        self._content = content
        self._fs = course_fs
        self._task_factory = task_factory
        self._legacy = legacy

        self._translations = {}
        translations_fs = self._fs.from_subfolder("$i18n")
        if translations_fs.exists():
            for f in translations_fs.list(folders=False, files=True, recursive=False):
                lang = f[0:len(f) - 3]
                if translations_fs.exists(lang + ".mo"):
                    self._translations[lang] = gettext.GNUTranslations(translations_fs.get_fd(lang + ".mo"))
                else:
                    self._translations[lang] = gettext.NullTranslations()

        try:
            self._name = self._content['name']
            self._admins = self._content.get('admins', [])
            self._description = self._content.get('description', '')
            self._public = self._content.get('public', False)
        except:
            raise Exception("Taskset has an invalid YAML spec: " + self.get_id())

    def get_translation_obj(self, language):
        return self._translations.get(language, gettext.NullTranslations())

    def gettext(self, language, *args, **kwargs):
        return self.get_translation_obj(language).gettext(*args, **kwargs)

    def get_id(self):
        """ Return the _id of this course """
        return self._id

    def get_fs(self):
        """ Returns a FileSystemProvider which points to the folder of this course """
        return self._fs

    def get_task(self, taskid):
        """ Returns a Task object """
        return self._task_factory.get_task(self, taskid)

    def get_descriptor(self):
        """ Get (a copy) the description of the course """
        return copy.deepcopy(self._content)

    def get_admins(self):
        """ Returns a list containing the usernames of the administrators of this course """
        return self._admins

    def get_tasks(self):
        """ Returns a dictionary of all the taskset tasks"""
        return self._task_factory.get_all_tasks(self)

    def get_name(self, language):
        """ Return the name of this course """
        return self.gettext(language, self._name) if self._name else ""

    def get_description(self, language):
        """Returns the course description """
        description = self.gettext(language, self._description) if self._description else ''
        return description

    def is_public(self):
        """Returns True if the taskset can be publicly instantiated"""
        return self._public

    def is_legacy(self):
        """ Returns if the taskset has been loaded via an old course.yaml file """
        return self._legacy
