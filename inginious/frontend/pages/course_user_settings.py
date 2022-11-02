# -*- coding: utf-8 -*-
"""
Module definition for CourseUserSettingPage class

This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
more information about the licensing of this file.
"""

import flask
from inginious.common.field_types import FieldTypes
from inginious.frontend.pages.utils import INGIniousAuthPage


class CourseUserSettingPage(INGIniousAuthPage):
    """
    Class definition for CourseUserSettingPage
    """

    def GET_AUTH(self, courseid):
        """ GET request """
        username = self.user_manager.session_username()
        if not self._is_accessible(courseid, username):
            return self.template_helper.render("course_unavailable.html")
        current_user = self.database.users.find_one(
            {"username": username})
        course_user_settings = current_user.get("course_settings", {})
        return self.show_page(courseid, course_user_settings.get(courseid, {}))

    def POST_AUTH(self, courseid):
        """ POST request """
        username = self.user_manager.session_username()
        if not self._is_accessible(courseid, username):
            return self.template_helper.render("course_unavailable.html")
        course_user_settings = self._sanitize_content(flask.request.form, courseid)
        if course_user_settings == {}:
            return self.show_page(courseid, {"error": ""})
        self.database.users.update_one({"username": username}, {"$set": {"course_settings." + courseid: course_user_settings}})

        return self.show_page(courseid, course_user_settings)

    def show_page(self, courseid, course_user_settings):
        """Definition of the show page method."""
        try:
            course = self.course_factory.get_course(courseid)
            course_user_setting_fields = course.get_additional_fields()
            return self.template_helper.render("course_user_settings.html", course=course,
                                               course_user_setting_fields=course_user_setting_fields,
                                               course_user_settings=course_user_settings, fieldtypes=FieldTypes)
        except Exception:
            return self.template_helper.render("course_unavailable.html")

    def _is_accessible(self, courseid, username):
        """
            Verify if course is accessible and that courseid match an existing course.
            :param: courseid - The id of the course.
            :param: username - The username of the logged user.
            :return: A boolean if the course is accessible for the given user.
        """
        try:
            course = self.course_factory.get_course(courseid)
            if not self.user_manager.course_is_user_registered(course, username):
                return False
            return True
        except Exception:
            return False

    def _sanitize_content(self, data, courseid):
        """
            Sanitize received data
            :param: data  - A dictionary that normally contains user settings for a course.
            :param: courseid - Id of the course.
            :return: A sanitized dict, an empty dict if something went wrong.
        """
        if not isinstance(data, dict):
            return {}
        copied_data = data.copy()
        course = self.course_factory.get_course(courseid)
        add_fields = course.get_additional_fields()
        for setting in data:
            error = False
            if setting not in add_fields:
                # if setting is not expected in the course definition. There is no reason to treat it.
                error = True
            if not error:
                try:
                    # we try to cast given value to be sure that we match expected type.
                    if add_fields[setting].get_type_name() == "STRING":
                        copied_data[setting] = str(data[setting])
                    elif add_fields[setting].get_type_name() == "INTEGER":
                        copied_data[setting] = int(data[setting])
                    else:
                        copied_data[setting] = bool(data[setting])
                except ValueError:
                    error = True
            if error:
                try:
                    copied_data.pop(setting)
                except Exception:
                    # should not happen as we are working on copy of iterated dict.
                    pass
        return copied_data.to_dict()
