# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class CourseSubmissionsNewPage(INGIniousAdminPage):
    """ Page that allow search, view, replay an download of submisssions done by students """

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)
        msgs = []

        return self.page(course, msgs)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)

        return self.page(course)

    def page(self, course, msgs=None):
        """ Get all data and display the page """
        msgs = msgs if msgs else []

        return self.template_helper.get_renderer().course_admin.new_submissions(course, msgs)