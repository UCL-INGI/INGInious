# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from inginious.common.field_types import FieldTypes


class AdditionalField:
    """
    This class represent extra field that can be added to a course.
    """

    def __init__(self, field_id, description, field_type):
        self._id = field_id
        self._description = description
        self._type = field_type

    def __eq__(self, other):
        return self._id == other._id

    def __hash__(self):
        return hash(self._id)

    def get_id(self):
        return self._id

    def get_description(self):
        return self._description

    def get_type_name(self):
        return FieldTypes(self._type).name

    def get_type(self):
        return self._type
