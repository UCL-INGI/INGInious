# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

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

        data = list(
            self.database.submissions.find({"username": {"$in": classroom["students"]}, "courseid": course.get_id(), "taskid": task.get_id()}).sort(
                [("submitted_on", pymongo.DESCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(course, str(f["_id"])))]) for f in data]
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
        submission = self.submission_manager.get_feedback_from_submission(submission, show_everything=True)

        if submission["classroomid"] != ObjectId(classroomid) or submission["courseid"] != course.get_id() or submission["taskid"] != task.get_id():
            return json.dumps({"status": "error", "text": "You do not have the rights to access to this submission"})
        elif "jobid" in submission:
            return json.dumps({"status": "ok", "text": "Submission is still running"})
        else:
            return json.dumps({"status": "ok", "data": submission}, default=str)
