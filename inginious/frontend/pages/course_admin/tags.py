# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


import json

import web
from bson.objectid import ObjectId

from inginious.frontend.pages.course_admin.utils import INGIniousSubmissionAdminPage


class CourseTagsPage(INGIniousSubmissionAdminPage):
    """ Replay operation management """

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        return self.show_page(course, web.input())

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        return self.show_page(course, web.input())

    def show_page(self, course, user_input):
        return self.template_helper.get_renderer().course_admin.tags(course)
