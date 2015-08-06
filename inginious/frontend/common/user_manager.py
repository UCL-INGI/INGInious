# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Manages users data and session """
from abc import ABCMeta, abstractmethod

class AbstractUserManager(object):

    __metaclass__ = ABCMeta

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

    @abstractmethod
    def get_task_status(self, task, username=None):
        """
        :param task: a Task object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: "succeeded" if the current user solved this task, "failed" if he failed, and "notattempted" if he did not try it yet
        """
        pass

    @abstractmethod
    def get_task_grade(self, task, username=None):
        """
        :param task: a Task object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: a floating point number (percentage of max grade)
        """
        pass
