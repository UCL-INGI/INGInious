# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


from collections import OrderedDict
import web
from inginious.frontend.webapp.pages.course_admin.utils import INGIniousSubmissionAdminPage


class CourseReplaySubmissions(INGIniousSubmissionAdminPage):
    """ Replay operation management """

    def POST(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        user_input = web.input(tasks=[], aggregations=[], users=[])

        # Check input
        tasks = course.get_tasks()
        for i in tasks:
            if i not in tasks.keys():
                raise web.notfound()

        # Load submissions
        submissions, _ = self.get_selected_submissions(course, user_input.filter_type, user_input.tasks, user_input.users, user_input.aggregations, user_input.type)
        for submission in submissions:
            self.submission_manager.replay_job(tasks[submission["taskid"]], submission)

        return self.show_page(course, web.input())

    def GET(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        return self.show_page(course, web.input())

    def show_page(self, course, user_input):
        # Load task list
        tasks, user_data, aggregations, tutored_aggregations,\
        tutored_users, checked_tasks, checked_users, show_aggregations = self.show_page_params(course, user_input)

        return self.template_helper.get_renderer().course_admin.replay(course,
                                                                         tasks, user_data, aggregations,
                                                                         tutored_aggregations, tutored_users,
                                                                         checked_tasks, checked_users,
                                                                         show_aggregations)
