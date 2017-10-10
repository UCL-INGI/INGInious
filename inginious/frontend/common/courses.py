# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Classes modifying basic tasks, problems and boxes classes """

import gettext
from inginious.common.courses import Course


class FrontendCourse(Course):
    """ A basic course extension that stores the name of the course """

    def __init__(self, courseid, content, course_fs, task_factory, hook_manager):
        super(FrontendCourse, self).__init__(courseid, content, course_fs, task_factory, hook_manager)

        try:
            self._name = self._content['name']
        except:
            raise Exception("Course has an invalid description: " + self.get_id())

        self._translations = {}
        translations_fs = self._fs.from_subfolder("$i18n")
        if translations_fs.exists():
            for f in translations_fs.list(folders=False, files=True, recursive=False):
                lang = f[0:len(f) - 3]
                if translations_fs.exists(lang + ".mo"):
                    self._translations[lang] = gettext.GNUTranslations(translations_fs.get_fd(lang + ".mo"))
                else:
                    self._translations[lang] = gettext.NullTranslations()

    def gettext(self, language, *args, **kwargs):
        translation = self._translations.get(language, gettext.NullTranslations())
        return translation.gettext(*args, **kwargs)

    def get_name(self, language):
        """ Return the name of this course """
        return self.gettext(language, self._name) if self._name else ""
