# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from bson.objectid import ObjectId
import web
import logging
from inginious.frontend.webapp.pages.course_admin.utils import INGIniousSubmissionAdminPage


class CourseDownloadSubmissions(INGIniousSubmissionAdminPage):
    """ Batch operation management """

    _logger = logging.getLogger("inginious.webapp.download")

    def valid_formats(self):
        return [
            "taskid/username",
            "taskid/aggregation",
            "username/taskid",
            "aggregation/taskid"
        ]

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)

        user_input = web.input(tasks=[], aggregations=[], users=[])

        if "filter_type" not in user_input or "type" not in user_input or "format" not in user_input or user_input.format not in self.valid_formats():
            raise web.notfound()

        tasks = list(course.get_tasks().keys())
        for i in user_input.tasks:
            if i not in tasks:
                raise web.notfound()

        # Load submissions
        submissions, aggregations = self.get_selected_submissions(course, user_input.filter_type, user_input.tasks,
                                                    user_input.users, user_input.aggregations, user_input.type)

        self._logger.info("Downloading %d submissions from course %s", len(submissions), courseid)
        web.header('Content-Type', 'application/x-gzip', unique=True)
        web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
        return self.submission_manager.get_submission_archive(submissions, list(reversed(user_input.format.split('/'))), aggregations)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        user_input = web.input()

        # First, check for a particular submission
        if "submission" in user_input:
            submission = self.database.submissions.find_one({"_id": ObjectId(user_input.submission),
                                                             "courseid": course.get_id(),
                                                             "status": {"$in": ["done", "error"]}})
            if submission is None:
                raise web.notfound()

            self._logger.info("Downloading submission %s - %s - %s - %s", submission['_id'], submission['courseid'],
                              submission['taskid'], submission['username'])
            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
            return self.submission_manager.get_submission_archive([submission], [], {})

        # Else, display the complete page

        tasks, user_data, aggregations, tutored_aggregations,\
        tutored_users, checked_tasks, checked_users, show_aggregations = self.show_page_params(course, user_input)

        chosen_format = self.valid_formats()[0]
        if "format" in user_input and user_input.format in self.valid_formats():
            chosen_format = user_input.format
            if "aggregation" in chosen_format:
                show_aggregations = True

        return self.template_helper.get_renderer().course_admin.download(course, tasks, user_data, aggregations,
                                                                         tutored_aggregations, tutored_users,
                                                                         checked_tasks, checked_users,
                                                                         self.valid_formats(), chosen_format,
                                                                         show_aggregations)
