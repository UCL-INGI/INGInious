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
from bson.objectid import ObjectId

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseClassroomInfoPage(INGIniousAdminPage):
    """ List information about a classroom """

    def GET(self, courseid, classroomid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        return self.page(course, classroomid)

    def submission_url_generator(self, course, classroomid, taskid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?format=taskid%2Fclassroom&tasks=" + taskid + "&classrooms=" + str(classroomid)

    def page(self, course, classroomid):
        """ Get all data and display the page """
        classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid)})

        data = list(self.database.submissions.aggregate(
            [
                {
                    "$match":
                        {
                            "courseid": course.get_id(),
                            "username": {"$in": classroom["students"]}
                        }
                },
                {
                    "$group":
                        {
                            "_id": "$taskid",
                            "tried": {"$sum": 1},
                            "succeeded": {"$sum": {"$cond": [{"$eq": ["$result", "success"]}, 1, 0]}},
                            "grade": {"$max": "$grade"}
                        }
                }
            ]))

        tasks = course.get_tasks()
        result = dict([(taskid, {"taskid": taskid, "name": tasks[taskid].get_name(), "tried": 0, "status": "notviewed",
                                 "grade": 0, "url": self.submission_url_generator(course, classroomid, taskid)}) for taskid in tasks])

        for taskdata in data:
            if taskdata["_id"] in result:
                result[taskdata["_id"]]["tried"] = taskdata["tried"]
                if taskdata["tried"] == 0:
                    result[taskdata["_id"]]["status"] = "notattempted"
                elif taskdata["succeeded"]:
                    result[taskdata["_id"]]["status"] = "succeeded"
                else:
                    result[taskdata["_id"]]["status"] = "failed"
                result[taskdata["_id"]]["grade"] = taskdata["grade"]

        if "csv" in web.input():
            return make_csv(result)

        return self.template_helper.get_renderer().course_admin.classroom(course, classroom, result.values())
