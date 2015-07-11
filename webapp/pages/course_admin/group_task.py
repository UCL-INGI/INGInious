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

from common_frontend.database import get_database
from common_frontend.templates import get_renderer
from webapp.pages.course_admin.utils import make_csv, get_course_and_check_rights
from webapp.submission_manager import get_submission

class CourseGroupTaskPage(object):
    """ List information about a task done by a student """

    def GET(self, courseid, groupid, taskid):
        """ GET request """
        course, task = get_course_and_check_rights(courseid, taskid)
        if not course.is_group_course():
            raise web.notfound()
        else:
            return self.page(course, groupid, task)

    def submission_url_generator(self, course, submissionid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?submission=" + submissionid

    def page(self, course, groupid, task):
        """ Get all data and display the page """
        data = list(get_database().submissions.find({"groupid": ObjectId(groupid), "courseid": course.get_id(), "taskid": task.get_id()}).sort(
            [("submitted_on", pymongo.DESCENDING)]))
        data = [dict(f.items() + [("url", self.submission_url_generator(course, str(f["_id"])))]) for f in data]
        if "csv" in web.input():
            return make_csv(data)

        group = get_database().groups.find_one({"_id": ObjectId(groupid)})
        return get_renderer.course_admin.group_task(course, group, task, data)


class SubmissionDownloadFeedback(object):
    def GET(self, courseid, groupid, taskid, submissionid):
        """ GET request """
        course, task = get_course_and_check_rights(courseid, taskid)

        if not course.is_group_course():
            raise web.notfound()
        else:
            return self.page(course, groupid, task, submissionid)

    def page(self, course, groupid, task, submissionid):
        submission = get_submission(submissionid, False)
        if submission["groupid"] != ObjectId(groupid) or submission["courseid"] != course.get_id() or submission["taskid"] != task.get_id():
            return json.dumps({"status": "error", "text": "You do not have the rights to access to this submission"})
        elif "jobid" in submission:
            return json.dumps({"status": "ok", "text": "Submission is still running"})
        else:
            return json.dumps({"status": "ok", "data": submission}, default=str)
