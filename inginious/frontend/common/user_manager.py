# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Manages users data and session """
from abc import ABCMeta, abstractmethod


class AbstractUserManager(object, metaclass=ABCMeta):
    @abstractmethod
    def session_logged_in(self):
        """ Returns True if a user is currently connected in this session, False else """
        pass

    @abstractmethod
    def session_username(self):
        """ Returns the username from the session, if one is open. Else, returns None"""
        pass

    @abstractmethod
    def session_email(self):
        """ Returns the email of the current user in the session, if one is open. Else, returns None"""
        pass

    @abstractmethod
    def session_realname(self):
        """ Returns the real name of the current user in the session, if one is open. Else, returns None"""
        pass