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
import pymongo
import web
from inginious.frontend.common.user_manager import AbstractUserManager


class UserManager(AbstractUserManager):
    def __init__(self, session_dict, database):
        """
        :type session_dict: web.session.Session
        :type database: pymongo.database.Database
        """
        self._session = session_dict
        self._database = database

    def session_logged_in(self):
        """ Returns True if a user is currently connected in this session, False else """
        return self._get_session_dict() is not None

    def session_username(self):
        """ Returns the username from the session, if one is open. Else, returns None"""
        if not self.session_logged_in():
            return None
        return self._get_session_dict()["username"]

    def session_email(self):
        """ Returns the email of the current user in the session, if one is open. Else, returns None"""
        if not self.session_logged_in():
            return None
        return self._get_session_dict()["email"]

    def session_realname(self):
        """ Returns the real name of the current user in the session, if one is open. Else, returns None"""
        if not self.session_logged_in():
            return None
        return self._get_session_dict()["realname"]

    def session_roles(self):
        """ Returns the LTI roles that the logged in user owns. If there are no user connected, returns []"""
        if not self.session_logged_in():
            return []
        return self._get_session_dict()["roles"]

    def session_task(self):
        """ Return a tuple (courseid, taskid), representing the task to which the current user is authenticated. If there are no user
        connected, returns None """
        if not self.session_logged_in():
            return None
        return self._get_session_dict()["task"]

    def session_consumer_key(self):
        """ Return the consumer key for the current context or None if no user is connected """
        if not self.session_logged_in():
            return None
        return self._get_session_dict()["consumer_key"]

    def session_outcome_service_url(self):
        """ Return the link to the outcome service url for the current context or None if no user is connected """
        if not self.session_logged_in():
            return None
        return self._get_session_dict()["outcome_service_url"]

    def session_outcome_result_id(self):
        """ Return the LIS outcome result id for the current context or None if no user is connected """
        if not self.session_logged_in():
            return None
        return self._get_session_dict()["outcome_result_id"]

    def lti_auth(self, session_identifier, user_id, roles, realname, email, course_id, task_id, consumer_key, outcome_service_url, outcome_result_id):
        """ LTI Auth """
        self._set_session_dict(session_identifier, {
            "email": email,
            "username": user_id,
            "realname": realname,
            "roles": roles,
            "task": (course_id, task_id),
            "outcome_service_url": outcome_service_url,
            "outcome_result_id": outcome_result_id,
            "consumer_key": consumer_key
        })

    def set_session_identifier(self, session_identifier):
        """ Define the current session identifier. Needed before calling anything else in user_manager (but internal methods and lti_auth)"""
        web.ctx.inginious_lti_session_identifier = session_identifier

    def _get_session_dict(self):
        if "inginious_lti_session_identifier" not in web.ctx:
            raise Exception("You cannot access methods from the user manager before calling set_session_identifier")
        if "sessions" not in self._session:
            return None
        return self._session["sessions"].get(web.ctx.inginious_lti_session_identifier)

    def _set_session_dict(self, session_identifier, value):
        if not "sessions" in self._session:
            self._session["sessions"] = {}
        self._session["sessions"][session_identifier] = value

    def get_task_status(self, task, username=None):
        """
        :param task: a Task object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: "succeeded" if the current user solved this task, "failed" if he failed, and "notattempted" if he did not try it yet
        """
        username = username or self.session_username()

        val = list(self._database.submissions.find({"username": username, "courseid": task.get_course_id(), "taskid": task.get_id(),
                                                    "status": "done"}).sort([("grade", pymongo.DESCENDING)]).limit(1))

        if len(val) == 1:
            if val[0]["result"] == "success":
                return "succeeded"
            else:
                return "failed"
        return "notattempted"

    def get_task_grade(self, task, username=None):
        """
        :param task: a Task object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: a floating point number (percentage of max grade)
        """
        username = username or self.session_username()

        val = list(self._database.submissions.find({"username": username, "courseid": task.get_course_id(), "taskid": task.get_id(),
                                                    "status": "done"}).sort([("grade",pymongo.DESCENDING)]).limit(1))
        if len(val) == 1:
            return float(val[0]["grade"])
        return 0.0
