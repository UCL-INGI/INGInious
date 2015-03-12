# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
import pymongo
import web

from inginious.frontend.base import get_database
from inginious.frontend.base import renderer
from inginious.frontend.pages.course_admin.utils import make_csv, get_course_and_check_rights


class CourseStudentTaskPage(object):

    """ List information about a task done by a student """

    def GET(self, courseid, username, taskid):
        """ GET request """
        course, task = get_course_and_check_rights(courseid, taskid)
        return self.page(course, username, task)

    def submission_url_generator(self, course, submissionid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/submissions?dl=submission&id=" + submissionid

    def page(self, course, username, task):
        """ Get all data and display the page """
        data = list(get_database().submissions.find({"username": username, "courseid": course.get_id(), "taskid": task.get_id()}).sort([("submitted_on", pymongo.DESCENDING)]))
        data = [dict(f.items() + [("url", self.submission_url_generator(course, str(f["_id"])))]) for f in data]
        if "csv" in web.input():
            return make_csv(data)
        return renderer.admin_course_student_task(course, username, task, data)
