# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.


import hashlib
import random
import web

from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage


class CourseDangerZonePage(INGIniousAdminPage):
    """ Course administration page: list of classrooms """

    def GET(self, courseid):
        """ GET request """
        if not self.user_manager.user_is_superadmin(self.user_manager.session_username()):
            raise web.notfound()

        course = self.course_factory.get_course(courseid)
        return self.page(course)

    def POST(self, courseid):
        """ POST request """
        if not self.user_manager.user_is_superadmin(self.user_manager.session_username()):
            raise web.notfound()

        msg = ""
        error = False

        data = web.input()
        if "wipeall" in data:
            if not data["token"] == self.user_manager.session_token():
                msg = "Operation aborted due to invalid token."
                error = True
            elif not data["courseid"] == courseid:
                msg = "Wrong course id."
                error = True
            else:
                msg = "All course data have been deleted."

        course = self.course_factory.get_course(courseid)
        return self.page(course, msg, error)

    def page(self, course, msg="", error=False):
        """ Get all data and display the page """
        thehash = hashlib.sha512(str(random.getrandbits(256))).hexdigest()
        self.user_manager.set_session_token(thehash)

        return self.template_helper.get_renderer().course_admin.danger_zone(course, thehash, msg, error)
