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
""" Pages that allow editing of tasks """

import web
from frontend.base import renderer
from frontend.pages.course_admin.utils import get_course_and_check_rights

from frontend.base import get_database
from bson.objectid import ObjectId

class CourseEditGroup(object):
    """ Edit a task """

    def GET(self, courseid, groupid):
        """ Edit a task """
        course, _ = get_course_and_check_rights(courseid, allow_all_staff=False)
        course_stud_list = course.get_registered_users(True)
        course_tut_list = course.get_staff(False)

        group = get_database().groups.find_one({"_id": ObjectId(groupid), "course_id": courseid})

        if group:
            return renderer.course_admin.edit_group(course, course_stud_list, course_tut_list, group, "", False)
        else:
            raise web.notfound()

    def POST(self, courseid, groupid):
        course, _ = get_course_and_check_rights(courseid, allow_all_staff=False)
        course_stud_list = course.get_registered_users(True)
        course_tut_list = course.get_staff(False)

        group = get_database().groups.find_one({"_id": ObjectId(groupid), "course_id": courseid})

        if not group:
            raise web.notfound()

        error = ""
        try:
            data = web.input()
            if not data['description']:
                error = 'No group description given.'
        except:
            error = 'User returned an invalid form.'

        return renderer.course_admin.edit_group(course, course_stud_list, course_tut_list, group, error, True)
