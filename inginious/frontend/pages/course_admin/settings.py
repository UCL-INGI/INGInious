# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import re
import flask

from inginious.common.base import dict_from_prefix, id_checker
from inginious.frontend.user_settings.field_types import FieldTypes
from inginious.frontend.accessible_time import AccessibleTime
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class CourseSettingsPage(INGIniousAdminPage):
    """ Couse settings """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)

        errors = []
        course_content = {}

        data = flask.request.form
        course_content = self.course_factory.get_course_descriptor_content(courseid)
        course_content['name'] = data['name']
        if course_content['name'] == "":
            errors.append(_('Invalid name'))
        course_content['description'] = data['description']
        course_content['admins'] = list(map(str.strip, data['admins'].split(','))) if data['admins'].strip() else []
        if not self.user_manager.user_is_superadmin() and self.user_manager.session_username() not in course_content['admins']:
            errors.append(_('You cannot remove yourself from the administrators of this course'))

        course_content['groups_student_choice'] = True if data["groups_student_choice"] == "true" else False

        if data["accessible"] == "custom":
            course_content['accessible'] = "{}/{}".format(data["accessible_start"], data["accessible_end"])
        elif data["accessible"] == "true":
            course_content['accessible'] = True
        else:
            course_content['accessible'] = False

        try:
            AccessibleTime(course_content['accessible'])
        except:
            errors.append(_('Invalid accessibility dates'))

        course_content['allow_unregister'] = True if data["allow_unregister"] == "true" else False
        course_content['allow_preview'] = True if data["allow_preview"] == "true" else False

        if data["registration"] == "custom":
            course_content['registration'] = "{}/{}".format(data["registration_start"], data["registration_end"])
        elif data["registration"] == "true":
            course_content['registration'] = True
        else:
            course_content['registration'] = False

        try:
            AccessibleTime(course_content['registration'])
        except:
            errors.append(_('Invalid registration dates'))

        course_content['registration_password'] = data['registration_password']
        if course_content['registration_password'] == "":
            course_content['registration_password'] = None

        course_content['registration_ac'] = data['registration_ac']
        if course_content['registration_ac'] not in ["None", "username", "binding", "email"]:
            errors.append(_('Invalid ACL value'))
        if course_content['registration_ac'] == "None":
            course_content['registration_ac'] = None

        course_content['registration_ac_accept'] = True if data['registration_ac_accept'] == "true" else False
        course_content['registration_ac_list'] = [line.strip() for line in data['registration_ac_list'].splitlines()]


        course_content['is_lti'] = 'lti' in data and data['lti'] == "true"
        course_content['lti_url'] = data.get("lti_url", "")
        course_content['lti_keys'] = dict([x.split(":") for x in data['lti_keys'].splitlines() if x])

        for lti_key in course_content['lti_keys'].keys():
            if not re.match("^[a-zA-Z0-9]*$", lti_key):
                errors.append(_("LTI keys must be alphanumerical."))

        course_content['lti_send_back_grade'] = 'lti_send_back_grade' in data and data['lti_send_back_grade'] == "true"

        tag_error = self.define_tags(course, data, course_content)
        if tag_error is not None:
            errors.append(tag_error)

        course_user_settings = self.define_course_user_settings(data)
        if course_user_settings is not None and not isinstance(course_user_settings, dict):
            errors.append(course_user_settings)
        course_content["fields"] = course_user_settings
        if len(errors) == 0:
            self.course_factory.update_course_descriptor_content(courseid, course_content)
            errors = None
            course, __ = self.get_course_and_check_rights(courseid)  # don't forget to reload the modified course

        return self.page(course, errors, errors is None)

    def page(self, course, errors=None, saved=False):
        """ Get all data and display the page """
        return self.template_helper.render("course_admin/settings.html", course=course, errors=errors, saved=saved,
                                           field_types=FieldTypes)

    def define_tags(self, course, data, course_content):
        tags = self.prepare_datas(data, "tags")
        if type(tags) is not dict:
            # prepare_datas returned an error
            return tags

        # Repair tags
        for key, tag in tags.items():
            # Since unchecked checkboxes are not present here, we manually add them to avoid later errors
            tag["visible"] = "visible" in tag
            tag["type"] = int(tag["type"])

            if (tag["id"] == "" and tag["type"] != 2) or tag["name"] == "":
                return _("Some tag fields were missing.")

            if not id_checker(tag["id"]):
                return _("Invalid tag id: {}").format(tag["id"])

            del tag["id"]

        course_content["tags"] = tags
        self.course_factory.update_course_descriptor_content(course.get_id(), course_content)

    def define_course_user_settings(self, data):
        """Course user settings definition method"""
        fields = self.prepare_datas(data, "field")
        if not isinstance(fields, dict):
            # prepare_datas returned an error
            return fields

        # Repair fields
        for field in fields.values():
            try:
                field["type"] = int(field["type"])
            except:
                return _("Invalid type value: {}").format(field["type"])
            if not id_checker(field["id"]):
                return _("Invalid id: {}").format(field["id"])

            del field["id"]
        return fields

    def prepare_datas(self, data, prefix: str):
        # prepare dict
        datas = dict_from_prefix(prefix, data)
        if datas is None:
            datas = {}

        items_id = [item["id"] for key, item in datas.items() if item["id"]]

        if len(items_id) != len(set(items_id)):
            return _("Some datas have the same id! The id must be unique.")

        return {field["id"]: field for item, field in datas.items() if field["id"]}

