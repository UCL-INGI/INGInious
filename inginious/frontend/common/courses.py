# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Classes modifying basic tasks, problems and boxes classes """
from inginious.common.courses import Course


class FrontendCourse(Course):
    """ A basic course extension that stores the name of the course """

    def __init__(self, courseid, content, task_factory, hook_manager):
        super(FrontendCourse, self).__init__(courseid, content, task_factory, hook_manager)

        try:
            self._name = self._content['name']
        except:
            raise Exception("Course has an invalid description: " + self.get_id())

    def get_name(self):
        """ Return the name of this course """
        return self._name
