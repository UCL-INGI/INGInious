# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Index page """

import logging

import web
from bson.objectid import ObjectId

from inginious.frontend.pages.utils import INGIniousAuthPage


class ClassroomPage(INGIniousAuthPage):
    """ Classroom page """

    _logger = logging.getLogger("inginious.webapp.classrooms")

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """

        course = self.course_factory.get_course(courseid)
        username = self.user_manager.session_username()

        error = False
        change = False
        msg = ""
        data = web.input()
        if self.user_manager.has_staff_rights_on_course(course):
            raise web.notfound()
        elif not self.user_manager.course_is_open_to_user(course, lti=False):
            return self.template_helper.get_renderer().course_unavailable()

        tasks = course.get_tasks()
        last_submissions = self.submission_manager.get_user_last_submissions(5, {"courseid": courseid, "taskid": {"$in": list(tasks.keys())}})
        for submission in last_submissions:
            submission["taskname"] = tasks[submission['taskid']].get_name(self.user_manager.session_language())

        classroom = self.user_manager.get_course_user_classroom(course)
        users = self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course))

        return self.template_helper.get_renderer().classroom(course, last_submissions, classroom, users,
                                                             msg, error, change)
