# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import flask
from inginious.frontend.pages.utils import INGIniousAuthPage


class CustomValuePage(INGIniousAuthPage):
    def GET_AUTH(self, courseid):
        """ GET request """
        username = self.user_manager.session_username()
        current_user = self.database.users.find_one(
            {"username": username})
        custom_values_user = current_user["custom"] if "custom" in current_user else {}
        return self.show_page(courseid, custom_values_user)

    def POST_AUTH(self, courseid):
        """ POST request """
        user_input = flask.request.form
        username = self.user_manager.session_username()
        current_user = self.database.users.find_one(
            {"username": username})
        custom_values_user = current_user["custom"] if "custom" in current_user else {}
        for key in user_input:
            custom_values_user[key] = user_input[key]
        removed_keys = list(set(custom_values_user.keys()) - set(user_input.keys()))
        for key in removed_keys:
            custom_values_user[key] = "off"
        self.database.users.update_one({"username": username}, {"$set": {"custom": custom_values_user}})

        return self.show_page(courseid, custom_values_user)

    def show_page(self, courseid, custom_values_user):
        course = self.course_factory.get_course(courseid)
        course_content = self.course_factory.get_course_descriptor_content(courseid)
        custom_fields = course_content["fields"] if "fields" in course_content else {}
        return self.template_helper.render("custom_values.html", course=course, custom_fields=custom_fields,
                                           custom_values_user=custom_values_user)

