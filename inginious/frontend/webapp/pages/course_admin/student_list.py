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

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseStudentListPage(INGIniousAdminPage):
    """ Course administration page: list of registered students """

    def GET(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def POST(self, courseid):
        """ POST request """
        course, _ = self.get_course_and_check_rights(courseid, None, False)
        data= web.input()
        if "remove" in data:
            try:
                if data["type"] == "all":
                    classrooms = list(self.database.classrooms.find({"courseid": courseid}))
                    for classroom in classrooms:
                        classroom["students"] = []
                        for group in classroom["groups"]:
                            group["students"] = []
                        self.database.classrooms.replace_one({"_id": classroom["_id"]}, classroom)
                else:
                    self.user_manager.course_unregister_user(course, data["username"])
            except:
                pass
        elif "register" in data:
            try:
                self.user_manager.course_register_user(course, data["username"], '', True)
            except:
                pass
        return self.page(course)

    def submission_url_generator(self, course, username):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?format=taskid%2Fusername&users=" + username

    def page(self, course, error="", post=False):
        """ Get all data and display the page """
        users = sorted(self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course, False)).items(),
                                   key=lambda k: k[1][0] if k[1] is not None else "")

        users = OrderedDict(sorted(self.user_manager.get_users_info(course.get_staff()).items(),
                                   key=lambda k: k[1][0] if k[1] is not None else "") + users)

        user_data = OrderedDict([(username, {
            "username": username, "realname": user[0] if user is not None else "",
            "email": user[1] if user is not None else "", "total_tasks": 0,
            "task_grades": {"answer": 0, "match": 0}, "task_succeeded": 0, "task_tried": 0, "total_tries": 0,
            "grade": 0, "url": self.submission_url_generator(course, username)}) for username, user in users.iteritems()])

        for username, data in self.user_manager.get_course_caches(users.keys(), course).iteritems():
            user_data[username].update(data if data is not None else {})

        if "csv" in web.input():
            return make_csv(user_data)

        return self.template_helper.get_renderer().course_admin.student_list(course, user_data.values(), error, post)
