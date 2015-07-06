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

from collections import OrderedDict
from frontend.base import renderer
from frontend.base import get_database
from frontend.pages.course_admin.utils import make_csv, get_course_and_check_rights
from frontend.user_data import UserData


class CourseGroupListPage(object):
    """ Course administration page: list of groups """

    def GET(self, courseid):
        """ GET request """
        course, _ = get_course_and_check_rights(courseid)
        if not course.is_group_course():
            raise web.notfound()
        else:
            return self.page(course)

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
        return "/admin/" + course.get_id() + "/submissions?dl=group&groupid=" + str(groupid)

    def page(self, course, error="", post=False):
        """ Get all data and display the page """
        groups = OrderedDict([(group['_id'], dict(group.items() + [("tried", 0), ("done", 0), ("url", self.submission_url_generator(course, group['_id']))])) for group in course.get_groups()])

        data = list(get_database().submissions.aggregate(
            [
                {
                    "$match":
                        {
                            "courseid": course.get_id(),
                            "groupid": {"$in": groups.keys()}
                        }
                },
                {
#,
                    "$group":
                        {
                            "_id": {"groupid": "$groupid", "taskid": "$taskid"},
                            "done": {"$sum": {"$cond": [{"$eq": ["$result", "success"]}, 1, 0]}}
                        }
                }
            ]))

        for group in data:
            groups[group["_id"]["groupid"]]["tried"] += 1
            groups[group["_id"]["groupid"]]["done"] += 1 if group["done"] else 0

        if "csv" in web.input():
            return make_csv(data)

        return renderer.course_admin.group_list(course, groups.values(), error, post)
