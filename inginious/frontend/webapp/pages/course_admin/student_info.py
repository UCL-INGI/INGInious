# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


import web

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseStudentInfoPage(INGIniousAdminPage):
    """ List information about a student """

    def GET_AUTH(self, courseid, username):  # pylint: disable=arguments-differ
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        return self.page(course, username)

    def submission_url_generator(self, username, taskid):
        """ Generates a submission url """
        return "?format=taskid%2Fusername&tasks=" + taskid + "&users=" + username

    def page(self, course, username):
        """ Get all data and display the page """
        data = list(self.database.user_tasks.find({"username": username, "courseid": course.get_id()}))

        tasks = course.get_tasks()
        result = dict([(taskid, {"taskid": taskid, "name": tasks[taskid].get_name(),
                                 "tried": 0, "status": "notviewed", "grade": 0,
                                 "url": self.submission_url_generator(username, taskid)}) for taskid in tasks])

        for taskdata in data:
            if taskdata["taskid"] in result:
                result[taskdata["taskid"]]["tried"] = taskdata["tried"]
                if taskdata["tried"] == 0:
                    result[taskdata["taskid"]]["status"] = "notattempted"
                elif taskdata["succeeded"]:
                    result[taskdata["taskid"]]["status"] = "succeeded"
                else:
                    result[taskdata["taskid"]]["status"] = "failed"
                result[taskdata["taskid"]]["grade"] = taskdata["grade"]
                result[taskdata["taskid"]]["submissionid"] = str(taskdata["submissionid"])

        if "csv" in web.input():
            return make_csv(result)

        results = sorted(list(result.values()), key=lambda result: (tasks[result["taskid"]].get_order(), result["taskid"]))
        return self.template_helper.get_renderer().course_admin.student_info(course, username, results)
