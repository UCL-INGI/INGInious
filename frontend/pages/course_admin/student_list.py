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
import web

from frontend.base import renderer
from frontend.base import get_database
from frontend.pages.course_admin.utils import make_csv, get_course_and_check_rights
from frontend.user_data import UserData


class CourseStudentListPage(object):
    """ Course administration page: list of registered students """

    def GET(self, courseid):
        """ GET request """
        course, _ = get_course_and_check_rights(courseid)
        return self.page(course)

    def submission_url_generator(self, course, username):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/submissions?dl=student&username=" + username

    def page(self, course, error="", post=False):
        """ Get all data and display the page """
        groups = []
        if course.is_group_course():
            groups = get_database().groups.find({"course_id": course.get_id()})
        groups = sorted(groups, key=lambda item: item["description"])

        groups.insert(0, {"_id": 0, "users": course.get_staff(), "description": "Course staff", "tutors": {}})

        user_data = UserData.get_course_data_for_users(course.get_id(), course.get_registered_users())
        for user in user_data.keys():
            user_data[user]["url"] = self.submission_url_generator(course, user)

        users_csv = [dict(f.items() + [("username", username)]) for username, f in user_data.iteritems()]

        if "csv" in web.input():
            return make_csv(users_csv)

        return renderer.course_admin.student_list(course, user_data, error, post)
