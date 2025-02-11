# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Beanie model for the User collection """
import re

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from beanie import Document


class User(Document):
    username : str
    realname : str
    email : str
    password : str

    bindings : dict[str, str] | None = {} # Don't need to use default_factory for non-hashable values with Pydantic
    language : str | None = "en" # default language needed ?
    activate : str | None = None # hash for account activation
    reset: str | None = None  # hash for password reset
    api_key : str | None = None
    tos_accepted : bool | None = False



    @model_validator(mode="before")
    @classmethod
    def is_defined_and_non_empty(cls, data):
        """
        Check if the field is defined and non-empty. Raise a ValueError if not. Does not apply to optional fields.
        """
        for field_name, field_value in data.items() :
            if field_name == "_id" :
                continue
            if cls.model_fields[field_name].is_required() and (field_value is None or field_value.strip() == "") :
                raise ValueError(f"Empty required field : {field_name}")
        return data


    @field_validator("username", mode="after")
    @classmethod
    def validate_username(cls, value):
        """
        Check if the username is at least 4 characters long and contains only letters, numbers, and a few special characters (-_|~).
        """
        if re.match(r"^[-_|~0-9A-Z]{4,}$", value, re.IGNORECASE) is None:
            raise ValueError(_("Invalid username format."))
        return value


    @field_validator("email", mode="after")
    @classmethod
    def sanitize_email(cls, value):
        """
        Sanitize an email address and put the bar part of an address foo@bar in lower case.
        """
        email_re = re.compile(
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
            r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain

        if email_re.match(value) is None:
            raise ValueError(_("Invalid email format."))

        email = value.split('@')
        return "%s@%s" % (email[0], email[1].lower())


    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, value):
        """
        Check if the password is at least 6 characters long.
        """
        if len(value) < 6:
            raise ValueError(_("Password too short."))
        return value

    class Settings :
        name = "users"
        #keep_nulls = False # to be added after code can handle user data that is not present in the DB

    class Config:
        arbitrary_types_allowed = True



