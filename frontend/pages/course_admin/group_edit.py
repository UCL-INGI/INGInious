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
from pymongo import ReturnDocument
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

        error = ""
        try:
            data = web.input(group_tutor=[],group_student=[])
            data["group_tutor"] = [tutor for tutor in data["group_tutor"] if tutor in course_tut_list]
            data["group_student"] = [student for student in data["group_student"] if student in course_stud_list]
            if data['description']:
                group = get_database().groups.find_one_and_update(
                    {"_id": ObjectId(groupid)},
                    {"$set": {"description": data["description"],
                              "users": data["group_student"], "tutors": data["group_tutor"]}},
                    return_document=ReturnDocument.AFTER)
            else:
                error = 'No group description given.'

        except:
            error = 'User returned an invalid form.'

        return renderer.course_admin.edit_group(course, course_stud_list, course_tut_list, group, error, True)
