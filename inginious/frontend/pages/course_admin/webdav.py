# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import web

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class WebDavInfoPage(INGIniousAdminPage):
    """ Explains how to access webdav """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def page(self, course):
        """ Get all data and display the page """
        if not self.webdav_host:
            raise web.notfound()

        url = self.webdav_host + "/" + course.get_id()
        username = self.user_manager.session_username()
        apikey = self.user_manager.session_api_key()
        return self.template_helper.get_renderer().course_admin.webdav(course, url, username, apikey)