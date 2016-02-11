# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


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
