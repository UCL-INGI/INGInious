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
from collections import OrderedDict

import web

from frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage

class CourseStudentListPage(INGIniousAdminPage):
    """ Course administration page: list of registered students """

    def GET(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def submission_url_generator(self, course, username):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?format=taskid%2Fusername&users=" + username

    def page(self, course, error="", post=False):
        """ Get all data and display the page """
        user_list = self.user_manager.get_course_registered_users(course)
        users = list(self.database.users.find({"_id": {"$in": user_list}}).sort("realname"))

        user_data = OrderedDict([(user["_id"], {
            "username": user["_id"], "realname": user["realname"], "email": user["email"], "total_tasks": 0,
            "task_grades": {"answer": 0, "match": 0}, "task_succeeded": 0, "task_tried": 0, "total_tries": 0,
            "grade": 0, "url": self.submission_url_generator(course, user["_id"])}) for user in users])

        for username, data in self.user_manager.get_course_caches(user_list, course).iteritems():
            user_data[username].update(data)

        if "csv" in web.input():
            return make_csv(user_data)

        return self.template_helper.get_renderer().course_admin.student_list(course, user_data.values(), error, post)
