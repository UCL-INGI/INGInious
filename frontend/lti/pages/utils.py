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
""" Some utils for all the pages """
from abc import abstractmethod
from oauth import oauth
from pylti.common import LTIOAuthDataStore, LTIException, verify_request_common
import web
import pylti

class LTIPage(object):
    """
    A base for all the pages of the INGInious LTI tool provider.
    Contains references to the PluginManager, the CourseFactory, and the SubmissionManager
    """

    def __init__(self, plugin_manager, course_factory, task_factory, submission_manager, user_manager, template_helper, database,
                 gridfs, default_allowed_file_extensions, default_max_file_size, containers):
        """
        Init the page
        :type plugin_manager: frontend.common.plugin_manager.PluginManager
        :type course_factory: common.course_factory.CourseFactory
        :type task_factory: common.task_factory.TaskFactory
        :type submission_manager: frontend.common.submission_manager.SubmissionManager
        :type user_manager: frontend.lti.user_manager.UserManager
        :type template_helper: frontend.common.template_helper.TemplateHelper
        :type database: pymongo.database.Database
        :type gridfs: gridfs.GridFS
        :type default_allowed_file_extensions: list(str)
        :type default_max_file_size: int
        :type containers: list(str)
        """
        self.plugin_manager = plugin_manager
        self.course_factory = course_factory
        self.task_factory = task_factory
        self.submission_manager = submission_manager
        self.user_manager = user_manager
        self.template_helper = template_helper
        self.database = database
        self.gridfs = gridfs
        self.default_allowed_file_extensions = default_allowed_file_extensions
        self.default_max_file_size = default_max_file_size
        self.containers = containers

class LTIAuthenticatedPage(LTIPage):
    """ A page that will be called by the TC or from an iframe within the TC """

    admin_role = ("Instructor", "Staff", "Administrator")
    tutor_role = ("Mentor",) + admin_role
    learner_role = ("Student", "Learner", "Member") + tutor_role

    def __init__(self, plugin_manager, course_factory, task_factory, submission_manager, user_manager, template_helper, database,
                 gridfs, default_allowed_file_extensions, default_max_file_size, containers):
        super(LTIAuthenticatedPage, self).__init__(plugin_manager, course_factory, task_factory, submission_manager, user_manager, template_helper, database,
        gridfs, default_allowed_file_extensions, default_max_file_size, containers)
        self.course = None
        self.task = None

    def LTI_POST(self, *args, **kwargs):
        raise web.notacceptable()

    def LTI_GET(self, *args, **kwargs):
        raise web.notacceptable()

    def required_role(self, method="POST"):
        """ Allow to override the minimal access right needed for this page. Method can be either "POST" or "GET" """
        return self.learner_role

    def verify_role(self, roles, method):
        for role in self.required_role(method):
            if role in roles:
                return True
        return False

    def POST(self, *args, **kwargs):
        try:
            self._verify_lti_status("POST")
        except Exception as e:
            raise web.notfound(str(e))
        return self.LTI_POST(*args, **kwargs)

    def GET(self, *args, **kwargs):
        try:
            self._verify_lti_status("GET")
        except Exception as e:
            raise web.notfound(str(e))
        return self.LTI_GET(*args, **kwargs)

    def _verify_lti_status(self, method="POST"):
        """ Verify session and/or parse the LTI data from the POST request """

        # First, check if a user is already logged-in
        user_logged_in = self.user_manager.session_logged_in()

        # Second, check if we are in a POST request including LTI data
        if method == "POST" and web.input().get("lti_message_type") == "basic-lti-launch-request":
            try:
                self._parse_lti_data()
            except:
                if not user_logged_in:
                    raise

        if not self.user_manager.session_logged_in():
            raise Exception("User not connected")

        if not self.verify_role(self.user_manager.session_roles(), method):
            raise Exception("User cannot see this page")

        try:
            course_id, task_id = self.user_manager.session_context()
            self.course = self.course_factory.get_course(course_id)
            self.task = self.course.get_task(task_id)
        except:
            raise Exception("Cannot find context")

    def _parse_lti_data(self):
        """ Verify and parse the data for the LTI basic launch """
        post_input = web.webapi.rawinput("POST")
        try:
            verified = verify_request_common({"__consumer_key__": {"secret": "__lti_secret__"}}, "http://localhost:8082/launch", "POST", {}, post_input)
        except:
            raise Exception("Cannot authentify request")

        if verified:
            user_id = post_input["user_id"]
            roles = post_input.get("roles", "Student").split(",")
            realname = self._find_realname(post_input)
            email = post_input.get("lis_person_contact_email_primary","")
            try:
                course_id, task_id = post_input["context_id"].split('/')
            except:
                raise Exception("Invalid context_id")

            self.user_manager.lti_auth(user_id, roles, realname, email, course_id, task_id)

    def _find_realname(self, post_input):
        """ Returns the most appropriate name to identify the user """

        # First, try the full name
        if "lis_person_name_full" in post_input:
            return post_input["lis_person_name_full"]
        if "lis_person_name_given" in post_input and "lis_person_name_family" in post_input:
            return post_input["lis_person_name_given"] + post_input["lis_person_name_family"]

        # Then the email
        if "lis_person_contact_email_primary" in post_input:
            return post_input["lis_person_contact_email_primary"]

        # Then only part of the full name
        if "lis_person_name_family" in post_input:
            return post_input["lis_person_name_family"]
        if "lis_person_name_given" in post_input:
            return post_input["lis_person_name_given"]

        return post_input["user_id"]