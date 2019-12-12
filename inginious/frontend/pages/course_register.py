# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Course page """
import web

from inginious.frontend.pages.utils import INGIniousAuthPage


class CourseRegisterPage(INGIniousAuthPage):
    """ Registers a user to a course """
    def basic_checks(self, courseid):
        try:
            course = self.course_factory.get_course(courseid)
        except:
            raise web.notfound()

        username = self.user_manager.session_username()
        user_info = self.user_manager.get_user_info(username)

        if self.user_manager.course_is_user_registered(course, username) or not course.is_registration_possible(user_info):
            raise web.seeother(self.app.get_homepath() + "/course/" + course.get_id())

        return course, username

    def GET_AUTH(self, courseid):
        course, _ = self.basic_checks(courseid)
        return self.template_helper.get_renderer(use_jinja=True).course_register(course=course, error=False)

    def POST_AUTH(self, courseid):
        course, username = self.basic_checks(courseid)
        user_input = web.input()
        success = self.user_manager.course_register_user(course, username, user_input.get("register_password", None))

        if success:
            raise web.seeother(self.app.get_homepath() + "/course/" + course.get_id())
        else:
            return self.template_helper.get_renderer(use_jinja=True).course_register(course=course, error=True)