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
from bson.objectid import ObjectId
import web

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseClassroomListPage(INGIniousAdminPage):
    """ Course administration page: list of classrooms """

    def GET(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def POST(self, courseid):
        """ POST request """
        course, _ = self.get_course_and_check_rights(courseid)

        error = False
        try:
            if self.user_manager.has_admin_rights_on_course(course):
                data = web.input()
                if 'classroom' in data:
                    default = True if self.database.classrooms.find_one({"courseid":courseid, "default": True}) is None else False
                    self.database.classrooms.insert({"default": default, "courseid": courseid, "students": [],
                                                     "tutors": [], "groups": [],
                                                     "description": data['classroom']})
                    msg = "New classroom created."
                elif 'default' in data:
                    self.database.classrooms.find_one_and_update({"courseid": courseid, "default": True},
                                                                 {"$set": {"default": False}})
                    self.database.classrooms.find_one_and_update({"_id": ObjectId(data['default'])},
                                                                 {"$set": {"default": True}})
                    msg = "Default classroom changed."
            else:
                msg = "You have no rights to add/change classrooms"
                error = True
        except:
            msg = 'User returned an invalid form.'
            error = True

        return self.page(course, msg, error)

    def submission_url_generator(self, course, classroomid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?format=taskid%2Fclassroom&classrooms=" + str(classroomid)

    def page(self, course, msg="", error=False):
        """ Get all data and display the page """
        classrooms = OrderedDict()

        for classroom in self.user_manager.get_course_classrooms(course):
            classrooms[classroom['_id']] = dict(classroom.items() +
                                                [("tried", 0),
                                                 ("done", 0),
                                                 ("url", self.submission_url_generator(course, classroom['_id']))
                                                 ])

            data = list(self.database.submissions.aggregate(
                [
                    {
                        "$match":
                            {
                                "courseid": course.get_id(),
                                "taskid": {"$in": course.get_tasks().keys()},
                                "username": {"$in": classroom["students"]}
                            }
                    },
                    {
                        "$group":
                            {
                                "_id": "$taskid",
                                "tried": {"$sum": 1},
                                "done": {"$sum": {"$cond": [{"$eq": ["$result", "success"]}, 1, 0]}}
                            }
                    },

                ]))

            for c in data:
                classrooms[classroom['_id']]["tried"] += 1 if c["tried"] else 0
                classrooms[classroom['_id']]["done"] += 1 if c["done"] else 0

        my_classrooms, other_classrooms = [], []
        for classroom in classrooms.values():
            if self.user_manager.session_username() in classroom["tutors"]:
                my_classrooms.append(classroom)
            else:
                other_classrooms.append(classroom)

        if "csv" in web.input():
            return make_csv(data)

        return self.template_helper.get_renderer().course_admin.classroom_list(course, [my_classrooms, other_classrooms], msg, error)
