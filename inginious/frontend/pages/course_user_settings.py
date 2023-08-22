# -*- coding: utf-8 -*-
"""
Module definition for CourseUserSettingPage class

This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
more information about the licensing of this file.
"""

import flask
from inginious.frontend.user_settings.field_types import FieldTypes
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
        return self.show_page(courseid, course_user_settings.get(courseid, {}), None)

    def POST_AUTH(self, courseid):
        """ POST request """
        username = self.user_manager.session_username()
        if not self._is_accessible(courseid, username):
            return self.template_helper.render("course_unavailable.html")
        try:
            course_user_settings = self._sanitize_content(flask.request.form, courseid)
        except Exception as e:
            feedback = ("danger", e)
            current_user = self.database.users.find_one(
                {"username": username})
            course_user_settings = current_user.get("course_settings", {})
            return self.show_page(courseid, course_user_settings.get(courseid, {}), feedback)

        self.database.users.update_one({"username": username},
                                       {"$set": {"course_settings." + courseid: course_user_settings}})

        return self.show_page(courseid, course_user_settings, ("success", "User settings successfully updated."))

    def show_page(self, courseid, course_user_settings, feedback):
        """
            Definition of the show page method.
            :param: courseid: the id of the course.
            :param: course_user_settings: The dict with the settings values.
            :param: feedback: a tuple with the type of feedback and the feedback. None if there is no feedback.
            :return:
        """
        try:
            course = self.course_factory.get_course(courseid)
            course_user_setting_fields = course.get_course_user_settings()
            return self.template_helper.render("course_user_settings.html", course=course,
                                               course_user_setting_fields=course_user_setting_fields,
                                               course_user_settings=course_user_settings, fieldtypes=FieldTypes,
                                               feedback=feedback)
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
            return self.user_manager.course_is_user_registered(course, username) \
                and self.user_manager.course_is_open_to_user(course, lti=False)
        except Exception:
            return False

    def _sanitize_content(self, data, courseid):
        """
            Sanitize received data
            :param: data  - A dictionary that normally contains user settings for a course.
            :param: courseid - Id of the course.
            :return: A sanitized dict.
        """
        if not isinstance(data, dict):
            raise TypeError("Incorrect type of data.")
        copied_data = {}
        course = self.course_factory.get_course(courseid)
        add_fields = course.get_course_user_settings()
        for field in add_fields:
            if field not in data:
                # setup default value.
                copied_data[field] = add_fields[field].get_cast_type()()
            else:
                try:
                    value = data[field]
                    if value is None or value == "":
                        value = add_fields[field].get_default_value()
                    # try to cast given value to be sure that we match expected type.
                    copied_data[field] = add_fields[field].get_cast_type()(value)
                except ValueError:
                    raise ValueError("Wrong value for field: " + str(field))
        return copied_data
