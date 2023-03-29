"""
Module definition for CourseUserSetting class

-*- coding: utf-8 -*-

This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
more information about the licensing of this file.
"""
from inginious.frontend.user_settings.field_types import FieldTypes


class CourseUserSetting:
    """
    This class represent settings for user in a course.
    """

    def __init__(self, field_id, description, field_type):
        self._id = field_id
        self._description = description
        if field_type in [field.value.id for field in FieldTypes]:
            self._type = field_type
        else:
            raise Exception("Field type not correct")

    def __eq__(self, other):
        return self._id == other._id

    def __hash__(self):
        return hash(self._id)

    def get_id(self):
        """
        :return: id of the setting
        """
        return self._id

    def get_description(self):
        """
        :return: description of the setting
        """
        return self._description

    def get_type_name(self):
        """"
        :return: type name of the setting
        """
        for ft in FieldTypes:
            if ft.value.id == self._type:
                return ft.name.lower()
        return ""

    def get_type(self):
        """
        :return: type of the setting
        """
        return self._type

    def get_cast_type(self):
        for ft in FieldTypes:
            if ft.value.id == self._type:
                return ft.value.cast_class

    def get_default_value(self):
        for ft in FieldTypes:
            if ft.value.id == self._type:
                return ft.value.default_value

    def render(self,template_helper,value):
        if self.get_type_name() !="":
            return template_helper.render("user_settings/"+self.get_type_name()+".html",input_id=self.get_id(),value=value or self.get_default_value())
        raise Exception