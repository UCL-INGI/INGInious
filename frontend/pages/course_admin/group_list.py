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


class CourseGroupListPage(object):
    """ Course administration page: list of groups """

    def GET(self, courseid):
        """ GET request """
        course, _ = get_course_and_check_rights(courseid)
        if course.is_group_course():
            return self.page(course)
        else:
            raise web.notfound()

    def POST(self, courseid):
        """ POST request """
        course, _ = get_course_and_check_rights(courseid)

        if not course.is_group_course():
            raise web.notfound()

        error = ""
        try:
            data = web.input()
            if not data['group_description']:
                error = 'No group description given.'
            else:
                get_database().groups.insert({"course_id": courseid, "users": [], "tutors": [], "size": 2,
                                              "description": data['group_description']})
        except:
            error = 'User returned an invalid form.'

        return self.page(course, error, True)

    def submission_url_generator(self, course, groupid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/submissions?dl=group&groupid=" + groupid

    def page(self, course, error="", newgroup=False):
        """ Get all data and display the page """
        non_empty_groups, empty_groups = [], []
        for group in list(get_database().groups.find({"course_id": course.get_id()})):
            (non_empty_groups if len(group["users"]) > 0 else empty_groups).append(group)

        # Group statistics corresponds to one of its member's statistics
        search_users = [group["users"][0] for group in non_empty_groups]
        data = UserData.get_course_data_for_users(course.get_id(), search_users)
        data = [dict(data[user].items() +
                     [("url", self.submission_url_generator(course, str(group["_id"]))),
                      ("description", group["description"]), ("group_id", group["_id"]),
                      ("percentage", int(course.get_user_grade(user)))])
                for group, user in zip(non_empty_groups, search_users) if user in data]

        data += [dict([("url", self.submission_url_generator(course, str(group["_id"]))),
                          ("description", group["description"]), ("group_id", group["_id"]),
                          ("percentage", 0), ("task_tried", 0), ("task_succeeded", 0)]) for group in empty_groups]

        data = sorted(data, key=lambda k: k['description'])

        if "csv" in web.input():
            return make_csv(data)
        return renderer.course_admin.group_list(course, data, error, newgroup)
