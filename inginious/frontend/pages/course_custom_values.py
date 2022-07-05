# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import flask
from inginious.frontend.pages.utils import INGIniousAuthPage


class CustomValuePage(INGIniousAuthPage):
    def GET_AUTH(self, courseid):
        """ GET request """
        course = self.course_factory.get_course(courseid)
        course_content = self.course_factory.get_course_descriptor_content(courseid)
        custom_fields = course_content["fields"] if "fields" in course_content else {}

        return self.template_helper.render("custom_values.html", course=course, custom_fields=custom_fields)

    def POST_AUTH(self, courseid):
        """ POST request """
        course = self.course_factory.get_course(courseid)

        user_input = flask.request.form
        print(user_input)
        return self.template_helper.render("maintenance.html")

