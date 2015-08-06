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
import json

import pymongo
import web
from bson.objectid import ObjectId

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseClassroomTaskPage(INGIniousAdminPage):
    """ List information about a task done by a student """

    def GET(self, courseid, classroomid, taskid):
        """ GET request """
        course, task = self.get_course_and_check_rights(courseid, taskid)
        return self.page(course, classroomid, task)

    def submission_url_generator(self, course, submissionid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?submission=" + submissionid

    def page(self, course, classroomid, task):
        """ Get all data and display the page """
        classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid)})

        data = list(self.database.submissions.find({"username": {"$in": classroom["students"]}, "courseid": course.get_id(), "taskid": task.get_id()}).sort(
            [("submitted_on", pymongo.DESCENDING)]))
        data = [dict(f.items() + [("url", self.submission_url_generator(course, str(f["_id"])))]) for f in data]
        if "csv" in web.input():
            return make_csv(data)

        return self.template_helper.get_renderer().course_admin.classroom_task(course, classroom, task, data)


class SubmissionDownloadFeedback(INGIniousAdminPage):
    def GET(self, courseid, classroomid, taskid, submissionid):
        """ GET request """
        course, task = self.get_course_and_check_rights(courseid, taskid)

        return self.page(course, classroomid, task, submissionid)

    def page(self, course, classroomid, task, submissionid):
        submission = self.submission_manager.get_submission(submissionid, False)
        submission = self.submission_manager.get_feedback_from_submission(submission)

        if submission["classroomid"] != ObjectId(classroomid) or submission["courseid"] != course.get_id() or submission["taskid"] != task.get_id():
            return json.dumps({"status": "error", "text": "You do not have the rights to access to this submission"})
        elif "jobid" in submission:
            return json.dumps({"status": "ok", "text": "Submission is still running"})
        else:
            return json.dumps({"status": "ok", "data": submission}, default=str)
