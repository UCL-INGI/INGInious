"""
Module definition for FieldTypes class

-*- coding: utf-8 -*-

This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
more information about the licensing of this file.
"""
from enum import Enum


class FieldTypes(Enum):
    """
    A class used to represent a field type. Based on Enums.
    """
    INTEGER = 1
    STRING = 2
    BOOLEAN = 3

    def get_cast_type(self):
        cast = [None, int, str, bool]
        return cast[self.value]
