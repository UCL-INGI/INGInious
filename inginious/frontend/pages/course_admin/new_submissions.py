# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import web
from collections import OrderedDict

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class CourseSubmissionsNewPage(INGIniousAdminPage):
    """ Page that allow search, view, replay an download of submisssions done by students """

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)
        msgs = []

        user_input = web.input(
            users=[],
            audiences=[]
        )
        params = self.get_params(user_input, course)

        return self.page(course, params, msgs)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        user_input = web.input(
            users=[],
            audiences=[]
        )
        params = self.get_params(user_input, course)

        return self.page(course, params)

    def page(self, course, params, msgs=None):
        """ Get all data and display the page """
        msgs = msgs if msgs else []

        users = self.get_users(course)
        audiences = self.user_manager.get_course_audiences(course)

        tutored_audiences = [str(audience["_id"]) for audience in audiences if
                             self.user_manager.session_username() in audience["tutors"]]
        tutored_users = []
        for audience in audiences:
            if self.user_manager.session_username() in audience["tutors"]:
                tutored_users += audience["students"]

        return self.template_helper.get_renderer().course_admin.new_submissions(course, users, tutored_users, audiences,
                                                                                tutored_audiences, params, msgs)

    def get_users(self, course):
        user_ids = self.user_manager.get_course_registered_users(course)
        users = {user: self.user_manager.get_user_realname(user) for user in user_ids}
        return OrderedDict(sorted(users.items(), key=lambda x: x[1]))

    def get_params(self, user_input, course):
        users = self.get_users(course)
        audiences = self.user_manager.get_course_audiences(course)

        # Sanitise user
        if not user_input.get("users", []) and not user_input.get("audiences", []):
            user_input["users"] = list(users.keys())
        if not isinstance(user_input.get("users", []), list):
            user_input["users"] = user_input["users"].split(',')
        user_input["users"] = [user for user in user_input["users"] if user in users]

        # Sanitise audiences
        if not isinstance(user_input.get("audiences", []), list):
            user_input["audiences"] = user_input["audiences"].split(',')
        user_input["audiences"] = [audience for audience in user_input["audiences"] if any(str(a["_id"]) == audience for a in audiences)]

        print(user_input)
        return user_input
