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
            audiences=[],
            tasks=[],
            org_tags=[]
        )
        params = self.get_params(user_input, course)

        return self.page(course, params, msgs)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        user_input = web.input(
            users=[],
            audiences=[],
            tasks=[],
            org_tags=[]
        )
        params = self.get_params(user_input, course)

        return self.page(course, params)

    def page(self, course, params, msgs=None):
        """ Get all data and display the page """
        msgs = msgs if msgs else []

        users = self.get_users(course)
        audiences = self.user_manager.get_course_audiences(course)
        tasks = course.get_tasks()

        tutored_audiences = [str(audience["_id"]) for audience in audiences if
                             self.user_manager.session_username() in audience["tutors"]]
        tutored_users = []
        for audience in audiences:
            if self.user_manager.session_username() in audience["tutors"]:
                tutored_users += audience["students"]

        return self.template_helper.get_renderer().course_admin.new_submissions(course, users, tutored_users, audiences,
                                                                                tutored_audiences, tasks, params, msgs)

    def get_users(self, course):
        user_ids = self.user_manager.get_course_registered_users(course)
        users = {user: self.user_manager.get_user_realname(user) for user in user_ids}
        return OrderedDict(sorted(users.items(), key=lambda x: x[1]))

    def get_params(self, user_input, course):
        users = self.get_users(course)
        audiences = self.user_manager.get_course_audiences(course)
        tasks = course.get_tasks()
        print(user_input)

        # Sanitise user
        if not user_input.get("users", []) and not user_input.get("audiences", []):
            user_input["users"] = list(users.keys())
        if len(user_input.get("users", [])) == 1 and "," in user_input["users"][0]:
            user_input["users"] = user_input["users"][0].split(',')
        user_input["users"] = [user for user in user_input["users"] if user in users]

        # Sanitise audiences
        if len(user_input.get("audiences", [])) == 1 and "," in user_input["audiences"][0]:
            user_input["audiences"] = user_input["audiences"][0].split(',')
        user_input["audiences"] = [audience for audience in user_input["audiences"] if any(str(a["_id"]) == audience for a in audiences)]

        # Sanitise tasks
        if not user_input.get("tasks", []):
            user_input["tasks"] = list(tasks.keys())
        if len(user_input.get("tasks", [])) == 1 and "," in user_input["tasks"][0]:
            user_input["tasks"] = user_input["tasks"][0].split(',')
        user_input["tasks"] = [task for task in user_input["tasks"] if task in tasks]

        # Sanitise tags
        if not user_input.get("tasks", []):
            user_input["tasks"] = []
        if len(user_input.get("org_tags", [])) == 1 and "," in user_input["org_tags"][0]:
            user_input["org_tags"] = user_input["org_tags"][0].split(',')
        print(course.get_tasks())
        user_input["org_tags"] = [org_tag for org_tag in user_input["org_tags"] if org_tag in course.get_tags()]

        print(user_input)
        return user_input
