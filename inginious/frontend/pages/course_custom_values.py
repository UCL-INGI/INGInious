"""
Module definition for CustomValuePage class
-*- coding: utf-8 -*-

This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
more information about the licensing of this file.
"""

import flask

from inginious.common.field_types import FieldTypes
from inginious.frontend.pages.utils import INGIniousAuthPage


class CustomValuePage(INGIniousAuthPage):
    """
    Class definition for CustomValuePage
    """

    def GET_AUTH(self, courseid):
        """ GET request """
        username = self.user_manager.session_username()
        current_user = self.database.users.find_one(
            {"username": username})
        custom_values_user = current_user.get("custom", {})
        return self.show_page(courseid, custom_values_user.get(courseid, {}))

    def POST_AUTH(self, courseid):
        """ POST request """
        user_input = flask.request.form
        username = self.user_manager.session_username()
        current_user = self.database.users.find_one(
            {"username": username})
        custom_values_user = current_user.get("custom", {}).get(courseid, {})
        custom_values_user.update(user_input)
        removed_keys = list(set(custom_values_user.keys()) - set(user_input.keys()))
        for key in removed_keys:
            del custom_values_user[key]
        self.database.users.update_one({"username": username}, {"$set": {"custom." + courseid: custom_values_user}})

        return self.show_page(courseid, custom_values_user)

    def show_page(self, courseid, custom_values_user):
        """Definition of the show page method."""
        course = self.course_factory.get_course(courseid)
        custom_fields = course.get_additional_fields()
        return self.template_helper.render("custom_values.html", course=course, custom_fields=custom_fields,
                                           custom_values_user=custom_values_user, fieldtypes=FieldTypes)
