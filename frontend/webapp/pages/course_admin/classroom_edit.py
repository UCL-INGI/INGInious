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
from pymongo import ReturnDocument
from bson.objectid import ObjectId

from frontend.webapp.pages.course_admin.utils import INGIniousAdminPage


class CourseEditGroup(INGIniousAdminPage):
    """ Edit a task """

    def get_user_lists(self, course, groupid):
        """ Get the available student and tutor lists for group edition"""
        student_list, tutor_list = self.user_manager.get_course_registered_users(course, False), course.get_staff()

        # Remove grouped users from the accessible list for the group
        grouped_users = self.database.groups.aggregate([
            {"$match": {"_id": {"$ne": ObjectId(groupid)}}},
            {"$group": {"_id": "$_id", "gusers": {"$addToSet": "$users"}}}])

        for result in grouped_users:
            for users in result["gusers"]:
                student_list = [student for student in student_list if student not in users]

        return student_list, tutor_list

    def GET(self, courseid, groupid):
        """ Edit a group """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        student_list, tutor_list = self.get_user_lists(course, groupid)

        group = self.database.groups.find_one({"_id": ObjectId(groupid), "course_id": courseid})

        if group:
            return self.template_helper.get_renderer().course_admin.edit_classroom(course, student_list, tutor_list, group, "", False)
        else:
            raise web.notfound()

    def POST(self, courseid, groupid):
        """ Edit a group """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        student_list, tutor_list = self.get_user_lists(course, groupid)
        group = self.database.groups.find_one({"_id": ObjectId(groupid), "course_id": courseid})

        error = ""
        try:
            data = web.input(group_tutor=[], group_student=[])
            if "delete" in data:
                self.database.groups.remove({"_id": ObjectId(groupid)})
                raise web.seeother("/admin/" + courseid + "/classrooms")
            else:
                data["group_tutor"] = [tutor for tutor in data["group_tutor"] if tutor in tutor_list]
                data["group_student"] = [student for student in data["group_student"] if student in student_list]

                if len(data["group_student"]) > int(data['size']):
                    error = 'Too many students for given group size.'
                elif data['description']:
                    group = self.database.groups.find_one_and_update(
                        {"_id": ObjectId(groupid)},
                        {"$set": {"description": data["description"],
                                  "users": data["group_student"], "tutors": data["group_tutor"],
                                  "size": abs(int(data["size"]))}}, return_document=ReturnDocument.AFTER)
                else:
                    error = 'No group description given.'
        except:
            error = 'User returned an invalid form.'

        return self.template_helper.get_renderer().course_admin.edit_classroom(course, student_list, tutor_list, group, error, True)
