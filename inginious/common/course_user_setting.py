"""
Module definition for CourseUserSetting class

-*- coding: utf-8 -*-

This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
more information about the licensing of this file.
"""
from inginious.common.field_types import FieldTypes


class CourseUserSetting:
    """
    This class represent settings for user in a course.
    """

    def __init__(self, field_id, description, field_type):
        self._id = field_id
        self._description = description
        if field_type in [field.value for field in FieldTypes]:
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
        return FieldTypes(self._type).name

    def get_type(self):
        """
        :return: type of the setting
        """
        return self._type

    def get_cast_type(self):
        return FieldTypes(self._type).get_cast_type()

    def render(self,value):
        content = "<input id='" + self.get_id() + "' name='" + self.get_id() + "'"
        if self.get_type_name() == 'BOOLEAN':
            content += " type='checkbox'"
            if value:
                content +=" checked"
        else:
            content += " class='form-control' value='{}' type='{}'"\
                .format(value,'text' if self.get_type_name() != 'INTEGER' else 'number')
        return content + ">"