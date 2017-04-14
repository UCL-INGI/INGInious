# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import pymongo
import web

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseStudentTaskPage(INGIniousAdminPage):
    """ List information about a task done by a student """

    def GET_AUTH(self, courseid, username, taskid):  # pylint: disable=arguments-differ
        """ GET request """
        course, task = self.get_course_and_check_rights(courseid, taskid)
        return self.page(course, username, task)

    def submission_url_generator(self, submissionid):
        """ Generates a submission url """
        return "?submission=" + submissionid

    def page(self, course, username, task):
        """ Get all data and display the page """
        data = list(self.database.submissions.find({"username": username, "courseid": course.get_id(), "taskid": task.get_id()}).sort(
            [("submitted_on", pymongo.DESCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(str(f["_id"])))]) for f in data]
        if "csv" in web.input():
            return make_csv(data)

        user_task = self.database.user_tasks.find_one({"username": username, "courseid": course.get_id(), "taskid": task.get_id()})
        submissionid = None if not user_task else user_task.get("submissionid", None)

        return self.template_helper.get_renderer().course_admin.student_task(course, username, task, data, submissionid)
