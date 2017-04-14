# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Manages users data and session """
import pymongo

from inginious.frontend.common.user_manager import AbstractUserManager


class UserManager(AbstractUserManager):
    def __init__(self, session, database, lti_user_name):
        """
        :type session: inginious.frontend.lti.custom_session.CustomSession
        :type database: pymongo.database.Database
        """
        self._session = session
        self._database = database
        self._lti_user_name = lti_user_name

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
            return None, None
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

    def lti_auth(self, user_id, roles, realname, email, course_id, task_id, consumer_key, outcome_service_url, outcome_result_id, ext_user_username):
        """ LTI Auth """
        self._set_session_dict({
            "email": email,
            "username": ext_user_username if self._lti_user_name == 'ext_user_username' else user_id,
            "realname": realname,
            "roles": roles,
            "task": (course_id, task_id),
            "outcome_service_url": outcome_service_url,
            "outcome_result_id": outcome_result_id,
            "consumer_key": consumer_key
        })

    def get_session_identifier(self):
        return self._session.session_id

    def set_session_identifier(self, session_identifier):
        """ Define the current session identifier. Needed before calling anything else in user_manager. If session_identifier is None,
        a new session is created """
        self._session.load(session_identifier)

    def _get_session_dict(self):
        if self._session.session_id is None:
            return None
        return self._session

    def _set_session_dict(self, value):
        if self._session.session_id is None:
            self.set_session_identifier(None)

        for key, val in value.items():
            self._session[key] = val

    def get_task_grade(self, task, username=None):
        """
        :param task: a Task object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: a floating point number (percentage of max grade)
        """
        username = username or self.session_username()
        grades = self._database.submissions.find({"username": username, "courseid": task.get_course_id(),
                                                  "taskid": task.get_id(), "status": "done"})

        if task.get_evaluate() == 'last':
            val = list(grades.sort([("submitted_on", pymongo.DESCENDING)]).limit(1))
        else:  # best : student selection is not supported here
            val = list(grades.sort([("grade", pymongo.DESCENDING)]).limit(1))

        return float(val[0]["grade"]) if len(val) == 1 else 0.0
