# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import json

import pymongo
import web

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseStudentTaskPage(INGIniousAdminPage):
    """ List information about a task done by a student """

    def GET(self, courseid, username, taskid):
        """ GET request """
        course, task = self.get_course_and_check_rights(courseid, taskid)
        return self.page(course, username, task)

    def submission_url_generator(self, course, submissionid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?submission=" + submissionid

    def page(self, course, username, task):
        """ Get all data and display the page """
        data = list(self.database.submissions.find({"username": username, "courseid": course.get_id(), "taskid": task.get_id()}).sort(
            [("submitted_on", pymongo.DESCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(course, str(f["_id"])))]) for f in data]
        if "csv" in web.input():
            return make_csv(data)
        return self.template_helper.get_renderer().course_admin.student_task(course, username, task, data)


class SubmissionDownloadFeedback(INGIniousAdminPage):
    def GET(self, courseid, username, taskid, submissionid):
        """ GET request """
        course, task = self.get_course_and_check_rights(courseid, taskid)
        return self.page(course, username, task, submissionid)

    def page(self, course, username, task, submissionid):
        submission = self.submission_manager.get_submission(submissionid, False)
        submission = self.submission_manager.get_feedback_from_submission(submission, show_everything=True)
        if username not in submission["username"] or submission["courseid"] != course.get_id() or submission["taskid"] != task.get_id():
            return json.dumps({"status": "error", "text": "You do not have the rights to access to this submission"})
        elif "jobid" in submission:
            return json.dumps({"status": "ok", "text": "Submission is still running"})
        else:
            return json.dumps({"status": "ok", "data": submission}, default=str)
