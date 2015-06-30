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

import web

from frontend.base import get_database
from frontend.base import renderer
from frontend.pages.course_admin.utils import make_csv, get_course_and_check_rights
from bson.objectid import ObjectId


class CourseGroupInfoPage(object):
    """ List information about a group """

    def GET(self, courseid, groupid):
        """ GET request """
        course, _ = get_course_and_check_rights(courseid)
        if course.is_group_course():
            return self.page(course, groupid)
        else:
            raise web.notfound()

    def submission_url_generator(self, course, username, taskid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/submissions?dl=group_task&task=" + taskid + "&groupid=" + username

    def page(self, course, groupid):
        """ Get all data and display the page """
        group = get_database().groups.find_one({"_id": ObjectId(groupid)})

        data = list(get_database().user_tasks.find({"username": group["users"][0] if len(group["users"]) > 0 else "", "courseid": course.get_id()}))
        tasks = course.get_tasks()
        result = OrderedDict()
        for taskid in tasks:
            result[taskid] = {"name": tasks[taskid].get_name(), "submissions": 0, "status": "notviewed",
                              "url": self.submission_url_generator(course, groupid, taskid)}
        for taskdata in data:
            if taskdata["taskid"] in result:
                result[taskdata["taskid"]]["submissions"] = taskdata["tried"]
                if taskdata["tried"] == 0:
                    result[taskdata["taskid"]]["status"] = "notattempted"
                elif taskdata["succeeded"]:
                    result[taskdata["taskid"]]["status"] = "succeeded"
                else:
                    result[taskdata["taskid"]]["status"] = "failed"
                result[taskdata["taskid"]]["grade"] = taskdata["grade"]

        if "csv" in web.input():
            return make_csv(result)

        return renderer.course_admin.group(course, group, result)
