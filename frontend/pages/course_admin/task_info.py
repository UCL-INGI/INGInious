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

from frontend.base import get_database
from frontend.base import renderer
from frontend.pages.course_admin.utils import make_csv, get_course_and_check_rights


class CourseTaskInfoPage(object):
    """ List informations about a task """

    def GET(self, courseid, taskid):
        """ GET request """
        course, task = get_course_and_check_rights(courseid, taskid)
        return self.page(course, task)

    def submission_url_generator(self, course, task, task_data):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/submissions?dl=student_task&username=" + task_data['username'] + "&task=" + task.get_id()

    def page(self, course, task):
        """ Get all data and display the page """

        groups = []
        if course.is_group_course():
            groups = get_database().groups.find({"course_id": course.get_id()})
        groups = sorted(groups, key=lambda item: item["description"])

        groups.insert(0, {"_id": 0, "users": course.get_staff(), "description": "Course staff", "tutors": {}})

        results = list(get_database().user_tasks.find({"courseid": course.get_id(), "taskid": task.get_id(),
                                                  "username": {"$in": course.get_registered_users()}}))
        data = {}
        for user in results:
            user["url"] = self.submission_url_generator(course, task, user)
            data[user["username"]] = user

        user_csv = [dict(data[key].items()) for key in data.keys()]
        if "csv" in web.input():
            return make_csv(user_csv)

        return renderer.course_admin.task_info(course, task, data, groups)
