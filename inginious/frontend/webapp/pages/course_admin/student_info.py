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

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseStudentInfoPage(INGIniousAdminPage):
    """ List information about a student """

    def GET(self, courseid, username):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        return self.page(course, username)

    def submission_url_generator(self, course, username, taskid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?format=taskid%2Fusername&tasks=" + taskid + "&users=" + username

    def page(self, course, username):
        """ Get all data and display the page """
        data = list(self.database.user_tasks.find({"username": username, "courseid": course.get_id()}))

        tasks = course.get_tasks()
        result = dict([(taskid, {"taskid": taskid, "name": tasks[taskid].get_name(),
                                 "tried": 0, "status": "notviewed", "grade": 0,
                                 "url": self.submission_url_generator(course, username, taskid)}) for taskid in tasks])

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

        if "csv" in web.input():
            return make_csv(result)
        return self.template_helper.get_renderer().course_admin.student(course, username, result.values())
