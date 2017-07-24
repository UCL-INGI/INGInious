# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Manages users data and session """
import logging
import hashlib
import web
from abc import ABCMeta, abstractmethod
from datetime import datetime
from datetime import timedelta
from functools import reduce
from natsort import natsorted
from collections import OrderedDict
import pymongo

from inginious.frontend.common.user_manager import AbstractUserManager


class AuthInvalidInputException(Exception):
    pass


class AuthInvalidMethodException(Exception):
    pass


class AuthMethod(object, metaclass=ABCMeta):

    @abstractmethod
    def get_id(self):
        """
        :return: The auth method id
        """
        return ""

    @abstractmethod
    def get_auth_link(self, user_manager):
        """
        :param user_manager: The user manager, for session storage
        :return: The authentication link
        """

    @abstractmethod
    def callback(self, user_manager):
        """
        :param user_manager: The user manager,  for session storage
        :return: User tuple, or None, if failed
        """

    @abstractmethod
    def get_name(self):
        """
        :return: The name of the auth method, to be displayed publicly
        """
        return ""

    @abstractmethod
    def get_imlink(self):
        """
        :return: The image link
        """
        return ""


class UserManager(AbstractUserManager):
    def __init__(self, session_dict, database, superadmins):
        """
        :type session_dict: web.session.Session
        :type database: pymongo.database.Database
        :type superadmins: list(str)
        :param superadmins: list of the super-administrators' usernames
        """
        self._session = session_dict
        self._database = database
        self._superadmins = superadmins
        self._auth_methods = OrderedDict()
        self._logger = logging.getLogger("inginious.webapp.users")

    ##############################################
    #           User session management          #
    ##############################################

    def session_logged_in(self):
        """ Returns True if a user is currently connected in this session, False else """
        return "loggedin" in self._session and self._session.loggedin is True

    def session_username(self):
        """ Returns the username from the session, if one is open. Else, returns None"""
        if not self.session_logged_in():
            return None
        return self._session.username

    def session_email(self):
        """ Returns the email of the current user in the session, if one is open. Else, returns None"""
        if not self.session_logged_in():
            return None
        return self._session.email

    def session_realname(self):
        """ Returns the real name of the current user in the session, if one is open. Else, returns None"""
        if not self.session_logged_in():
            return None
        return self._session.realname

    def session_token(self):
        """ Returns the token of the current user in the session, if one is open. Else, returns None"""
        if not self.session_logged_in():
            return None
        return self._session.token

    def session_lti_info(self):
        """ If the current session is an LTI one, returns a dict in the form 
            {
                "email": email,
                "username": username
                "realname": realname,
                "roles": roles,
                "task": (course_id, task_id),
                "outcome_service_url": outcome_service_url,
                "outcome_result_id": outcome_result_id,
                "consumer_key": consumer_key
            }
            where all these data where provided by the LTI consumer, and MAY NOT be equivalent to the data
            contained in database for the currently connected user.
            
            If the current session is not an LTI one, returns None.
        """
        if "lti" in self._session:
            return self._session.lti
        return None

    def session_cookieless(self):
        """ Indicates if the current session is cookieless """
        return self._session.get("cookieless", False)

    def session_id(self):
        """ Returns the current session id"""
        return self._session.get("session_id", "")

    def session_redir_url(self):
        """ Returns the redirection url for login """
        return self._session.get("redir_url", "")

    def session_oauth_state(self):
        """ Returns the oauth state for login """
        return self._session.get("oauth_state", None)

    def set_session_token(self, token):
        """ Sets the token of the current user in the session, if one is open."""
        if self.session_logged_in():
            self._session.token = token

    def set_session_realname(self, realname):
        """ Sets the real name of the current user in the session, if one is open."""
        if self.session_logged_in():
            self._session.realname = realname

    def set_session_redir_url(self, redir_url):
        """ Sets the redirection url for login """
        self._session.redir_url = redir_url

    def set_session_oauth_state(self, oauth_state):
        """Sets the oauth state for login """
        self._session.oauth_state = oauth_state

    def _set_session(self, username, realname, email):
        """ Init the session. Preserves potential LTI information. """
        self._session.loggedin = True
        self._session.email = email
        self._session.username = username
        self._session.realname = realname
        self._session.token = None
        if "lti" not in self._session:
            self._session.lti = None

    def _destroy_session(self):
        """ Destroy the session """
        self._session.loggedin = False
        self._session.email = None
        self._session.username = None
        self._session.realname = None
        self._session.token = None
        self._session.lti = None

    def create_lti_session(self, user_id, roles, realname, email, course_id, task_id, consumer_key, outcome_service_url,
                           outcome_result_id, tool_name, tool_desc, tool_url, context_title, context_label):
        """ Creates an LTI cookieless session. Returns the new session id"""

        self._destroy_session()  # don't forget to destroy the current session (cleans the threaded dict from web.py)
        self._session.load('')  # creates a new cookieless session
        session_id = self._session.session_id

        self._session.lti = {
            "email": email,
            "username": user_id,
            "realname": realname,
            "roles": roles,
            "task": (course_id, task_id),
            "outcome_service_url": outcome_service_url,
            "outcome_result_id": outcome_result_id,
            "consumer_key": consumer_key,
            "context_title": context_title,
            "context_label": context_label,
            "tool_description": tool_desc,
            "tool_name": tool_name,
            "tool_url": tool_url
        }

        return session_id

    def attempt_lti_login(self):
        """ Given that the current session is an LTI one (session_lti_info does not return None), attempt to find an INGInious user
            linked to this lti username/consumer_key. If such user exists, logs in using it.
             
            Returns True (resp. False) if the login was successful
        """
        if "lti" not in self._session:
            raise Exception("Not an LTI session")

        # TODO allow user to be automagically connected if the TC uses the same user id
        return False

    ##############################################
    #      User searching and authentication     #
    ##############################################

    def register_auth_method(self, auth_method):
        """
        Registers an authentication method
        :param auth_method: an AuthMethod object
        """
        self._auth_methods[auth_method.get_id()] = auth_method

    def get_auth_method(self, auth_method_id):
        """
        :param the auth method id, as provided by get_auth_methods_inputs()
        :return: AuthMethod if it exists, otherwise None
        """
        return self._auth_methods.get(auth_method_id, None)

    def get_auth_methods(self):
        """
        :return: The auth methods dict
        """
        return self._auth_methods

    def auth_user(self, username, password):
        """
        Authenticate the user in database
        :param username: Username/Login
        :param password: User password
        :return: Returns a dict represrnting the user
        """
        password_hash = hashlib.sha512(password.encode("utf-8")).hexdigest()

        user = self._database.users.find_one(
            {"username": username, "password": password_hash, "activate": {"$exists": False}})

        return user if user is not None and self.connect_user(username, user["realname"], user["email"]) else None

    def connect_user(self, username, realname, email):
        """
        Opens a session for the user
        :param username: Username
        :param realname: User real name
        :param email: User email
        """

        self._database.users.update_one({"username": username}, {"$set": {"realname": realname, "email": email}},
                                        upsert=True)
        self._logger.info("User %s connected - %s - %s - %s", username, realname, email, web.ctx.ip)
        self._set_session(username, realname, email)
        return True

    def disconnect_user(self):
        """
        Disconnects the user currently logged-in
        :param ip_addr: the ip address of the client, that will be logged
        """
        if self.session_logged_in():
            self._logger.info("User %s disconnected - %s - %s - %s", self.session_username(), self.session_realname(), self.session_email(), web.ctx.ip)
        self._destroy_session()

    def get_users_info(self, usernames):
        """
        :param usernames: a list of usernames
        :return: a dict, in the form {username: val}, where val is either None if the user cannot be found, or a tuple (realname, email)
        """
        retval = {username: None for username in usernames}
        remaining_users = usernames

        infos = self._database.users.find({"username": {"$in": remaining_users}})
        for info in infos:
            retval[info["username"]] = (info["realname"], info["email"])

        return retval

    def get_user_info(self, username):
        """
        :param username:
        :return: a tuple (realname, email) if the user can be found, None else
        """
        info = self.get_users_info([username])
        return info[username] if info is not None else None

    def get_user_realname(self, username):
        """
        :param username:
        :return: the real name of the user if it can be found, None else
        """
        info = self.get_user_info(username)
        if info is not None:
            return info[0]
        return None

    def get_user_email(self, username):
        """
        :param username:
        :return: the email of the user if it can be found, None else
        """
        info = self.get_user_info(username)
        if info is not None:
            return info[1]
        return None

    ##############################################
    #      User task/course info management      #
    ##############################################

    def get_course_cache(self, username, course):
        """
        :param username: The username
        :param course: A Course object
        :return: a dict containing info about the course, in the form:

            ::

                {"task_tried": 0, "total_tries": 0, "task_succeeded": 0, "task_grades":{"task_1": 100.0, "task_2": 0.0, ...}}

            Note that only the task already seen at least one time will be present in the dict task_grades.
        """
        return self.get_course_caches([username], course)[username]

    def get_course_caches(self, usernames, course):
        """
        :param username: List of username for which we want info. If usernames is None, data from all users will be returned.
        :param course: A Course object
        :return:
            Returns data of the specified users for a specific course. users is a list of username.

            The returned value is a dict:

            ::

                {"username": {"task_tried": 0, "total_tries": 0, "task_succeeded": 0, "task_grades":{"task_1": 100.0, "task_2": 0.0, ...}}}

            Note that only the task already seen at least one time will be present in the dict task_grades.
        """

        match = {"courseid": course.get_id()}
        if usernames is not None:
            match["username"] = {"$in": usernames}

        tasks = course.get_tasks()
        taskids = tasks.keys()
        match["taskid"] = {"$in": list(taskids)}

        data = list(self._database.user_tasks.aggregate(
            [
                {"$match": match},
                {"$group": {
                    "_id": "$username",
                    "task_tried": {"$sum": {"$cond": [{"$ne": ["$tried", 0]}, 1, 0]}},
                    "total_tries": {"$sum": "$tried"},
                    "task_succeeded": {"$addToSet": {"$cond": ["$succeeded", "$taskid", False]}},
                    "task_grades": {"$addToSet": {"taskid": "$taskid", "grade": "$grade"}}
                }}
            ]))

        student_visible_taskids = [taskid for taskid, task in tasks.items() if task.get_accessible_time().after_start()]
        course_staff = course.get_staff()
        retval = {username: {"task_succeeded": 0, "task_grades": [], "grade": 0} for username in usernames}

        for result in data:
            username = result["_id"]
            visible_tasks = student_visible_taskids if username not in course_staff else taskids
            result["task_succeeded"] = len(set(result["task_succeeded"]).intersection(visible_tasks))
            result["task_grades"] = {dg["taskid"]: dg["grade"] for dg in result["task_grades"] if dg["taskid"] in visible_tasks}

            total_weight = 0
            grade = 0
            for task_id in visible_tasks:
                total_weight += tasks[task_id].get_grading_weight()
                grade += result["task_grades"].get(task_id, 0.0) * tasks[task_id].get_grading_weight()

            result["grade"] = round(grade / total_weight) if total_weight > 0 else 0
            retval[username] = result

        return retval

    def get_task_cache(self, username, courseid, taskid):
        """
        Shorthand for get_task_caches([username], courseid, taskid)[username]
        """
        return self.get_task_caches([username], courseid, taskid)[username]

    def get_task_caches(self, usernames, courseid, taskid):
        """
        :param usernames: List of username for which we want info. If usernames is None, data from all users will be returned.
        :param courseid: the course id
        :param taskid: the task id
        :return: A dict in the form:

            ::

                {
                    "username": {
                        "courseid": courseid,
                        "taskid": taskid,
                        "tried": 0,
                        "succeeded": False,
                        "grade": 0.0
                    }
                }
        """
        match = {"courseid": courseid, "taskid": taskid}
        if usernames is not None:
            match["username"] = {"$in": usernames}

        data = self._database.user_tasks.find(match)
        retval = {username: None for username in usernames}
        for result in data:
            username = result["username"]
            del result["username"]
            del result["_id"]
            retval[username] = result

        return retval

    def user_saw_task(self, username, courseid, taskid):
        """ Set in the database that the user has viewed this task """
        self._database.user_tasks.update({"username": username, "courseid": courseid, "taskid": taskid},
                                         {"$setOnInsert": {"username": username, "courseid": courseid, "taskid": taskid,
                                                           "tried": 0, "succeeded": False, "grade": 0.0, "submissionid": None}},
                                         upsert=True)

    def update_user_stats(self, username, task, submission, result_str, grade, newsub):
        """ Update stats with a new submission """
        self.user_saw_task(username, submission["courseid"], submission["taskid"])

        if newsub:
            old_submission = self._database.user_tasks.find_one_and_update(
                {"username": username, "courseid": submission["courseid"], "taskid": submission["taskid"]}, {"$inc": {"tried": 1, "tokens.amount": 1}})

            # Check if the submission is the default download
            set_default = task.get_evaluate() == 'last' or \
                          (task.get_evaluate() == 'student' and old_submission is None) or \
                          (task.get_evaluate() == 'best' and old_submission.get('grade', 0.0) <= grade)

            if set_default:
                self._database.user_tasks.find_one_and_update(
                    {"username": username, "courseid": submission["courseid"], "taskid": submission["taskid"]},
                    {"$set": {"succeeded": result_str == "success", "grade": grade, "submissionid": submission['_id']}})
        else:
            old_submission = self._database.user_tasks.find_one(
                {"username": username, "courseid": submission["courseid"], "taskid": submission["taskid"]})

            if task.get_evaluate() == 'best':  # if best, update cache consequently (with best submission)
                def_sub = list(self._database.submissions.find({
                    "username": username, "courseid": task.get_course_id(),
                    "taskid": task.get_id(), "status": "done"}
                ).sort([("grade", pymongo.DESCENDING), ("submitted_on", pymongo.DESCENDING)]).limit(1))

                if len(def_sub) > 0:
                    self._database.user_tasks.find_one_and_update(
                        {"username": username, "courseid": submission["courseid"], "taskid": submission["taskid"]},
                        {"$set": {"succeeded": def_sub[0]["result"] == "success", "grade": def_sub[0]["grade"], "submissionid": def_sub[0]['_id']}})
            elif old_submission["submissionid"] == submission["_id"]:  # otherwise, update cache if needed
                self._database.user_tasks.find_one_and_update(
                    {"username": username, "courseid": submission["courseid"], "taskid": submission["taskid"]},
                    {"$set": {"succeeded": submission["result"] == "success", "grade": submission["grade"]}})

    def task_is_visible_by_user(self, task, username=None, lti=None):
        """ Returns true if the task is visible by the user
        :param lti: indicates if the user is currently in a LTI session or not.
            - None to ignore the check
            - True to indicate the user is in a LTI session
            - False to indicate the user is not in a LTI session
            - "auto" to enable the check and take the information from the current session
        """
        if username is None:
            username = self.session_username()

        return (self.course_is_open_to_user(task.get_course(), username, lti) and task.get_accessible_time().after_start()) or \
               self.has_staff_rights_on_course(task.get_course(), username)

    def task_can_user_submit(self, task, username=None, only_check=None, lti=None):
        """ returns true if the user can submit his work for this task
            :param only_check : only checks for 'groups', 'tokens', or None if all checks
            :param lti: indicates if the user is currently in a LTI session or not.
            - None to ignore the check
            - True to indicate the user is in a LTI session
            - False to indicate the user is not in a LTI session
            - "auto" to enable the check and take the information from the current session
        """
        if username is None:
            username = self.session_username()

        # Check if course access is ok
        course_registered = self.course_is_open_to_user(task.get_course(), username, lti)
        # Check if task accessible to user
        task_accessible = task.get_accessible_time().is_open()
        # User has staff rights ?
        staff_right = self.has_staff_rights_on_course(task.get_course(), username)

        # Check for group
        aggregation = self._database.aggregations.find_one(
            {"courseid": task.get_course_id(), "groups.students": self.session_username()},
            {"groups": {"$elemMatch": {"students": self.session_username()}}})

        if not only_check or only_check == 'groups':
            group_filter = (aggregation is not None and task.is_group_task()) or not task.is_group_task()
        else:
            group_filter = True

        students = aggregation["groups"][0]["students"] if (aggregation is not None and task.is_group_task()) else [self.session_username()]


        # Check for token availability
        enough_tokens = True
        timenow = datetime.now()
        submission_limit = task.get_submission_limit()
        if not only_check or only_check == 'tokens':
            if submission_limit == {"amount": -1, "period": -1}:
                # no token limits
                enough_tokens = True
            else:
                # select users with a cache for this particular task
                user_tasks = list(self._database.user_tasks.find({"courseid": task.get_course_id(),
                                                                  "taskid": task.get_id(),
                                                                  "username": {"$in": students}}))

                # verify that they all can submit
                def check_tokens_for_user_task(user_task):
                    token_dict = user_task.get("tokens", {"amount": 0, "date": datetime.fromtimestamp(0)})
                    tokens_ok = token_dict.get("amount", 0) < submission_limit["amount"]
                    date_limited = submission_limit["period"] > 0
                    need_reset = token_dict.get("date", datetime.fromtimestamp(0)) < timenow - timedelta(hours=submission_limit["period"])

                    if date_limited and need_reset:
                        # time limit for the tokens is reached; reset the tokens
                        self._database.user_tasks.find_one_and_update(user_task, {"$set": {"tokens": {"amount": 0, "date": datetime.now()}}})
                        return True
                    elif tokens_ok:
                        return True
                    else:
                        return False

                enough_tokens = reduce(lambda old,user_task: old and check_tokens_for_user_task(user_task), user_tasks, True)

        return (course_registered and task_accessible and group_filter and enough_tokens) or staff_right

    def get_course_aggregations(self, course):
        """ Returns a list of the course aggregations"""
        return natsorted(list(self._database.aggregations.find({"courseid": course.get_id()})), key=lambda x: x["description"])

    def get_course_user_aggregation(self, course, username=None):
        """ Returns the classroom whose username belongs to
        :param course: a Course object
        :param username: The username of the user that we want to register. If None, uses self.session_username()
        :return: the classroom description
        """
        if username is None:
            username = self.session_username()

        return self._database.aggregations.find_one({"courseid": course.get_id(), "students": username})

    def course_register_user(self, course, username=None, password=None, force=False):
        """
        Register a user to the course
        :param course: a Course object
        :param username: The username of the user that we want to register. If None, uses self.session_username()
        :param password: Password for the course. Needed if course.is_password_needed_for_registration() and force != True
        :param force: Force registration
        :return: True if the registration succeeded, False else
        """
        if username is None:
            username = self.session_username()

        realname, email = self.get_user_info(username)

        if not force:
            if not course.is_registration_possible(username, realname, email):
                return False
            if course.is_password_needed_for_registration() and course.get_registration_password() != password:
                return False
        if self.course_is_open_to_user(course, username):
            return False  # already registered?

        aggregation = self._database.aggregations.find_one({"courseid": course.get_id(), "default": True})
        if aggregation is None:
            self._database.aggregations.insert({"courseid": course.get_id(), "description": "Default classroom",
                                              "students": [username], "tutors": [], "groups": [], "default": True})
        else:
            self._database.aggregations.find_one_and_update({"courseid": course.get_id(), "default": True},
                                                          {"$push": {"students": username}})

        self._logger.info("User %s registered to course %s", username, course.get_id())
        return True

    def course_unregister_user(self, course, username=None):
        """
        Unregister a user to the course
        :param course: a Course object
        :param username: The username of the user that we want to unregister. If None, uses self.session_username()
        """
        if username is None:
            username = self.session_username()

        # Needed if user belongs to a group
        self._database.aggregations.find_one_and_update(
            {"courseid": course.get_id(), "groups.students": username},
            {"$pull": {"groups.$.students": username, "students": username}})

        # If user doesn't belong to a group, will ensure correct deletion
        self._database.aggregations.find_one_and_update(
            {"courseid": course.get_id(), "students": username},
            {"$pull": {"students": username}})

        self._logger.info("User %s unregistered from course %s", username, course.get_id())

    def course_is_open_to_user(self, course, username=None, lti=None):
        """
        Checks if a user is can access a course
        :param course: a Course object
        :param username: The username of the user that we want to check. If None, uses self.session_username()
        :param lti: indicates if the user is currently in a LTI session or not.
            - None to ignore the check
            - True to indicate the user is in a LTI session
            - False to indicate the user is not in a LTI session
            - "auto" to enable the check and take the information from the current session
        :return: True if the user can access the course, False else
        """
        if username is None:
            username = self.session_username()
        if lti == "auto":
            lti = self.session_lti_info() is not None

        if self.has_staff_rights_on_course(course, username):
            return True

        if not course.get_accessibility().is_open() or not self.course_is_user_registered(course, username):
            return False

        if lti is not None and course.is_lti() != lti:
            return False

        return True

    def course_is_user_registered(self, course, username=None):
        """
        Checks if a user is registered
        :param course: a Course object
        :param username: The username of the user that we want to check. If None, uses self.session_username()
        :return: True if the user is registered, False else
        """
        if username is None:
            username = self.session_username()

        if self.has_staff_rights_on_course(course, username):
            return True

        return self._database.aggregations.find_one({"students": username, "courseid": course.get_id()}) is not None

    def get_course_registered_users(self, course, with_admins=True):
        """
        Get all the users registered to a course
        :param course: a Course object
        :param with_admins: include admins?
        :return: a list of usernames that are registered to the course
        """

        l = [entry['students'] for entry in list(self._database.aggregations.aggregate([
            {"$match": {"courseid": course.get_id()}},
            {"$unwind": "$students"},
            {"$project": {"_id": 0, "students": 1}}
        ]))]
        if with_admins:
            return list(set(l + course.get_staff()))
        else:
            return l

    ##############################################
    #             Rights management              #
    ##############################################

    def user_is_superadmin(self, username=None):
        """
        :param username: the username. If None, the username of the currently logged in user is taken
        :return: True if the user is superadmin, False else
        """
        if username is None:
            username = self.session_username()

        return username in self._superadmins

    def has_admin_rights_on_course(self, course, username=None, include_superadmins=True):
        """
        Check if a user can be considered as having admin rights for a course
        :type course: webapp.custom.courses.WebAppCourse
        :param username: the username. If None, the username of the currently logged in user is taken
        :param include_superadmins: Boolean indicating if superadmins should be taken into account
        :return: True if the user has admin rights, False else
        """
        if username is None:
            username = self.session_username()

        return (username in course.get_admins()) or (include_superadmins and self.user_is_superadmin(username))

    def has_staff_rights_on_course(self, course, username=None, include_superadmins=True):
        """
        Check if a user can be considered as having staff rights for a course
        :type course: webapp.custom.courses.WebAppCourse
        :param username: the username. If None, the username of the currently logged in user is taken
        :param include_superadmins: Boolean indicating if superadmins should be taken into account
        :return: True if the user has staff rights, False else
        """
        if username is None:
            username = self.session_username()

        return (username in course.get_staff()) or (include_superadmins and self.user_is_superadmin(username))
