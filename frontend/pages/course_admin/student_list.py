# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
from frontend.pages.course_admin.utils import make_csv, get_course_and_check_rights
from frontend.user_data import UserData


class CourseStudentListPage(object):

    """ Course administration page: list of registered students """

    def GET(self, courseid):
        """ GET request """
        course = get_course_and_check_rights(courseid)
        return self.page(course)

    def submission_url_generator(self, course, username):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/submissions?dl=student&username=" + username

    def page(self, course):
        """ Get all data and display the page """
        data = UserData.get_course_data_for_users(course.get_id(), course.get_registered_users())
        data = [dict(f.items() + [("url", self.submission_url_generator(course, username)), ("username", username)]) for username, f in data.iteritems()]
        if "csv" in web.input():
            return make_csv(data)
        return renderer.admin_course_student_list(course, data)
