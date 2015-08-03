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
from frontend.common.user_manager import AbstractUserManager


class UserManager(AbstractUserManager):

    def session_logged_in(self):
        """ Returns True if a user is currently connected in this session, False else """
        return True

    def session_username(self):
        """ Returns the username from the session, if one is open. Else, returns None"""
        return "test"

    def session_email(self):
        """ Returns the email of the current user in the session, if one is open. Else, returns None"""
        return "test@test.be"

    def session_realname(self):
        """ Returns the real name of the current user in the session, if one is open. Else, returns None"""
        return "test"

    def session_roles(self):
        """ Returns the LTI roles that the logged in user owns"""
        return 'Student',

    def session_context(self):
        """ Return a tuple courseid, taskid, representing the LTI context to which the current user is authenticated """
        return "test", "test"

    def lti_auth(self, user_id, roles, realname, email, course_id, task_id):
        """
        LTI Auth
        :param user_id:
        :param roles:
        :param realname:
        :param email:
        :param course_id:
        :param task_id:
        :return:
        """
        pass

    def get_users_info(self, usernames):
        """
        :param usernames: a list of usernames
        :return: a dict, in the form {username: val}, where val is either None if the user cannot be found, or a tuple (realname, email)
        """
        if "test" in usernames:
            return {"test": ("test", "test@test.be")}
        else:
            return {}

    def get_user_info(self, username):
        """
        :param username:
        :return: a tuple (realname, email) if the user can be found, None else
        """
        if username == "test":
            return "test", "test@test.be"
        return None

    def get_user_realname(self, username):
        """
        :param username:
        :return: the real name of the user if it can be found, None else
        """
        if username == "test":
            return "test"
        return None

    def get_user_email(self, username):
        """
        :param username:
        :return: the email of the user if it can be found, None else
        """
        if username == "test":
            return "test@test.be"
        return None

    def get_task_status(self, task, username=None):
        """
        :param task: a Task object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: "succeeded" if the current user solved this task, "failed" if he failed, and "notattempted" if he did not try it yet
        """
        return "notattempted"

    def get_task_grade(self, task, username=None):
        """
        :param task: a Task object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: a floating point number (percentage of max grade)
        """
        return 0.0