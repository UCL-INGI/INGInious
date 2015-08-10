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
from datetime import datetime
from inginious.frontend.common.user_manager import AbstractUserManager


class AuthInvalidInputException(Exception):
    pass


class AuthInvalidMethodException(Exception):
    pass


class AuthMethod(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_name(self):
        """
        :return: The name of the auth method, to be displayed publicly
        """
        return ""

    @abstractmethod
    def auth(self, user_input):
        """
        :param user_input: the input of the user, respecting the value given by self.needed_input()
        :return: (username, realname, email) if the user credentials are correct, None else
        """
        return None

    @abstractmethod
    def needed_fields(self):
        """
        :return: a dictionary containing as key the name of the input (in the HTML sense of name), and, as value, a dictionary containing two fields:

            placeholder
                the placeholder for the input

            type
                text or password
        """
        return {}

    def should_cache(self):
        """
        :return: True if the results of the get_user(s)_info methods should be cached
        """
        return True

    def get_user_info(self, username):
        """
        :param username:
        :return: (realname, email) if the user is available with this auth method, None else
        """
        info = self.get_users_info([username])
        return info[username] if info is not None else None

    @abstractmethod
    def get_users_info(self, usernames):
        """
        :param usernames: a list of usernames
        :return: a dict containing key/pairs {username: (realname, email)} if the user is available with this auth method,
            {username: None} else
        """
        return None


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
        self._auth_methods = []

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

    def _set_session(self, username, realname, email):
        """ Init the session """
        self._session.loggedin = True
        self._session.email = email
        self._session.username = username
        self._session.realname = realname

    def _destroy_session(self):
        """ Destroy the session """
        self._session.loggedin = False
        self._session.email = None
        self._session.username = None
        self._session.realname = None

    ##############################################
    #      User searching and authentication     #
    ##############################################

    def register_auth_method(self, auth_method):
        """
        Registers an authentication method
        :param auth_method: an AuthMethod object
        """
        self._auth_methods.append(auth_method)

    def get_auth_methods_fields(self):
        """
        :return: a dict, containing the auth method id as key, and a tuple (name, needed fields) for each auth method
        """
        return {i: (am.get_name(), am.needed_fields()) for i, am in enumerate(self._auth_methods)}

    def auth_user(self, auth_method_id, input):
        """
        :param auth_method_id: the auth method id, as provided by get_auth_methods_inputs()
        :param input: the input of the user, should respect what was given by get_auth_methods_inputs()
        :raise AuthInvalidInputException
        :return: True if the user successfully authenticated, False else
        """
        if len(self._auth_methods) <= auth_method_id:
            raise AuthInvalidMethodException()
        info = self._auth_methods[auth_method_id].auth(input)
        if info is not None:
            self._set_session(info[0], info[1], info[2])
            return True
        return False

    def disconnect_user(self):
        """ Disconnects the user currently logged-in """
        self._destroy_session()

    def get_users_info(self, usernames):
        """
        :param usernames: a list of usernames
        :return: a dict, in the form {username: val}, where val is either None if the user cannot be found, or a tuple (realname, email)
        """
        retval = {username: None for username in usernames}
        remaining_users = usernames

        # First, look in non cached auth methods for the user
        for method in self._auth_methods:
            if method.should_cache() is False:
                infos = method.get_users_info(remaining_users)
                for user, val in infos.iteritems():
                    retval[user] = val

        remaining_users = [username for username, val in retval.iteritems() if val is None]
        if len(remaining_users) == 0:
            return retval

        # If this is not the case, look in the cache
        infos = self._database.user_info_cache.find({"_id": {"$in": remaining_users}})
        for info in infos:
            retval[info["_id"]] = (info["realname"], info["email"])

        remaining_users = [username for username, val in retval.iteritems() if val is None]
        if len(remaining_users) == 0:
            return retval

        # If it's still not the case, ask the other auth methods
        for method in self._auth_methods:
            if method.should_cache() is True:
                infos = method.get_users_info(remaining_users)
                for user, val in infos.iteritems():
                    if val is not None:
                        retval[user] = val
                        self._database.user_info_cache.update_one({"_id": user}, {"$set": {"realname": val[0], "email": val[1]}}, upsert=True)

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
        match["taskid"] = {"$in": tasks.keys()}

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

        user_tasks = [taskid for taskid, task in tasks.iteritems() if task.get_accessible_time().after_start()]

        retval = {username: None for username in usernames}
        for result in data:
            result["total_tasks"] = len(user_tasks)
            result["task_succeeded"] = len(set(result["task_succeeded"]).intersection(user_tasks))
            result["task_grades"] = {dg["taskid"]: dg["grade"] for dg in result["task_grades"] if dg["taskid"] in user_tasks}

            total_weight = 0
            grade = 0

            for task_id in user_tasks:
                total_weight += tasks[task_id].get_grading_weight()
                grade += result["task_grades"].get(task_id, 0.0) * tasks[task_id].get_grading_weight()

            result["grade"] = int(grade / total_weight) if total_weight > 0 else 0

            username = result["_id"]
            del result["_id"]
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
                                                           "tried": 0, "succeeded": False, "grade": 0.0}},
                                         upsert=True)

    def update_user_stats(self, username, submission, job):
        """ Update stats with a new submission """
        self.user_saw_task(username, submission["courseid"], submission["taskid"])

        # Update inc counter
        self._database.user_tasks.update({"username": username, "courseid": submission["courseid"], "taskid": submission["taskid"]},
                                         {"$inc": {"tried": 1}})

        # Set to succeeded if not succeeded yet
        if job["result"] == "success":
            self._database.user_tasks.find_and_modify({"username": username, "courseid": submission["courseid"], "taskid": submission["taskid"],
                                                       "succeeded": False},
                                                      {"$set": {"succeeded": True}})

            # Update the grade if needed
            self._database.user_tasks.find_and_modify({"username": username, "courseid": submission["courseid"], "taskid": submission["taskid"],
                                                       "grade": {"$lt": job["grade"]}}, {"$set": {"grade": job["grade"]}})

    def get_course_grade(self, course, username=None):
        """
        :param course: a Course object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: a floating point number (percentage of max grade)
        """
        if username is None:
            username = self.session_username()

        cache = self.get_course_cache(username, course)
        if cache is None:
            return 0
        total_weight = 0
        grade = 0

        for task_id, task in course.get_tasks().iteritems():
            if self.task_is_visible_by_user(task, username):
                total_weight += task.get_grading_weight()
                grade += cache["task_grades"].get(task_id, 0.0) * task.get_grading_weight()

        if total_weight == 0:
            return 0

        return grade / total_weight

    def get_task_status(self, task, username=None):
        """
        :param task: a Task object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: "succeeded" if the current user solved this task, "failed" if he failed, and "notattempted" if he did not try it yet
        """
        if username is None:
            username = self.session_username()

        task_cache = self.get_task_cache(username, task.get_course_id(), task.get_id())
        if task_cache is None:
            return "notviewed"
        if task_cache["tried"] == 0:
            return "notattempted"
        return "succeeded" if task_cache["succeeded"] else "failed"

    def get_task_grade(self, task, username=None):
        """
        :param task: a Task object
        :param username: The username of the user for who we want to retrieve the grade. If None, uses self.session_username()
        :return: a floating point number (percentage of max grade)
        """
        if username is None:
            username = self.session_username()

        task_cache = self.get_task_cache(username, task.get_course_id(), task.get_id())
        if task_cache is None:
            return 0.0
        return task_cache.get("grade", 0.0)

    def task_is_visible_by_user(self, task, username=None):
        """ Returns true if the task is visible by the user """
        if username is None:
            username = self.session_username()

        return (self.course_is_open_to_user(task.get_course(), username) and task._accessible.after_start()) or \
               self.has_staff_rights_on_course(task.get_course(), username)

    def task_can_user_submit(self, task, username=None):
        """ returns true if the user can submit his work for this task """
        if username is None:
            username = self.session_username()

        classroom = self._database.classrooms.find_one({"courseid": task.get_course_id(), "groups.students": username})
        group_filter = (classroom is not None and task.is_group_task()) or not task.is_group_task()

        return (self.course_is_open_to_user(task.get_course(), username) and task._accessible.is_open() and group_filter) or self.has_staff_rights_on_course(
            task.get_course(), username)

    def get_course_classrooms(self, course):
        """ Returns a list of the course classrooms"""
        return list(self._database.classrooms.find({"courseid": course.get_id()}).sort("description"))

    def get_course_user_classroom(self, course, username=None):
        """ Returns the classroom whose username belongs to
        :param course: a Course object
        :param username: The username of the user that we want to register. If None, uses self.session_username()
        :return: the classroom description
        """
        if username is None:
            username = self.session_username()

        return self._database.classrooms.find_one({"courseid": course.get_id(), "students": username})

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
            if course.is_password_needed_for_registration() and course._registration_password != password:
                return False
        if self.course_is_open_to_user(course, username):
            return False  # already registered?

        classroom = self._database.classrooms.find_one({"courseid": course.get_id(), "default": True})
        if classroom is None:
            self._database.classrooms.insert({"courseid": course.get_id(), "description": "Default classroom",
                                              "students": [username], "tutors": [],  "groups": [], "default": True})
        else:
            self._database.classrooms.find_one_and_update({"courseid": course.get_id(), "default": True},
                                                          {"$push": {"students": username}})

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
        self._database.classrooms.find_one_and_update(
            {"courseid": course.get_id(), "groups.students": username},
            {"$pull": {"groups.$.students": username, "students": username}})

        # If user doesn't belong to a group, will ensure correct deletion
        self._database.classrooms.find_one_and_update(
            {"courseid": course.get_id(), "students": username},
            {"$pull": {"students": username}})

    def course_is_open_to_user(self, course, username=None):
        """
        Checks if a user is can access a course
        :param course: a Course object
        :param username: The username of the user that we want to check. If None, uses self.session_username()
        :return: True if the user can access the course, False else
        """
        if username is None:
            username = self.session_username()

        return (course._accessible.is_open() and self.course_is_user_registered(course, username))\
               or self.has_staff_rights_on_course(course, username)

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

        return self._database.classrooms.find_one({"students": username, "courseid": course.get_id()}) is not None

    def get_course_registered_users(self, course, with_admins=True):
        """
        Get all the users registered to a course
        :param course: a Course object
        :param with_admins: include admins?
        :return: a list of usernames that are registered to the course
        """

        l = [entry['students'] for entry in list(self._database.classrooms.aggregate([
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
