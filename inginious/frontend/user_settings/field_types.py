"""
Module definition for FieldTypes class

-*- coding: utf-8 -*-

This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
more information about the licensing of this file.
"""
from enum import Enum
from collections import namedtuple

Types = namedtuple("Types",["id","cast_class","default_value"])

class FieldTypes(Enum):
    """
    A class used to represent a field type. Based on Enums.
    """
    INTEGER = Types(1,int,0)
    STRING = Types(2,str,"")
    BOOLEAN = Types(3,bool,False)
