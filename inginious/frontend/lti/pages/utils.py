# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some utils for all the pages """
import abc
import hashlib
from typing import List, Dict

from gridfs import GridFS
# from pylti.common import verify_request_common TODO re-add me once PR has been accepted by PyLTI devs
from inginious.common.customlibs.pylti import verify_request_common
import web
from pymongo.database import Database

from inginious.common.course_factory import CourseFactory
from inginious.common.task_factory import TaskFactory
from inginious.frontend.common.plugin_manager import PluginManager
from inginious.frontend.common.submission_manager import SubmissionManager
from inginious.frontend.common.template_helper import TemplateHelper
from inginious.frontend.lti.user_manager import UserManager


class LTIPage(object):
    """
    A base for all the pages of the INGInious LTI tool provider.
    Contains references to the PluginManager, the CourseFactory, and the SubmissionManager
    """

    @property
    def app(self):
        return web.ctx.app_stack[0]

    @property
    def plugin_manager(self) -> PluginManager:
        return self.app.plugin_manager

    @property
    def course_factory(self) -> CourseFactory:
        return self.app.course_factory

    @property
    def task_factory(self) -> TaskFactory:
        return self.app.task_factory

    @property
    def submission_manager(self) -> SubmissionManager:
        return self.app.submission_manager

    @property
    def user_manager(self) -> UserManager:
        return self.app.user_manager

    @property
    def template_helper(self) -> TemplateHelper:
        return self.app.template_helper

    @property
    def database(self) -> Database:
        return self.app.database

    @property
    def gridfs(self) -> GridFS:
        return self.app.gridfs

    @property
    def default_allowed_file_extensions(self) -> List[str]:
        return self.app.default_allowed_file_extensions

    @property
    def default_max_file_size(self) -> int:
        return self.app.default_max_file_size

    @property
    def containers(self) -> List[str]:
        return self.app.submission_manager.get_available_environments()

    @property
    def consumers(self) -> Dict[str, Dict[str, str]]:
        return self.app.consumers


class LTINotConnectedException(Exception):
    pass


class LTINoRightsException(Exception):
    pass


class LTIAuthenticatedPage(LTIPage):
    """ A page that needs to be authentified by the TC """

    admin_role = ("Instructor", "Staff", "Administrator")
    tutor_role = ("Mentor",) + admin_role
    learner_role = ("Student", "Learner", "Member") + tutor_role

    def __init__(self):
        super(LTIAuthenticatedPage, self).__init__()
        self.course = None
        self.task = None

    def LTI_POST(self, *args, **kwargs):
        raise web.notacceptable()

    def LTI_GET(self, *args, **kwargs):
        raise web.notacceptable()

    def LTI_GET_NOT_CONNECTED(self, *args, **kwargs):
        raise web.notfound("Your session expired. Please reload the page.")

    def LTI_POST_NOT_CONNECTED(self, *args, **kwargs):
        raise web.notfound("Your session expired. Please reload the page.")

    def LTI_GET_NO_RIGHTS(self, *args, **kwargs):
        raise web.notfound("You do not have the rights to view this page.")

    def LTI_POST_NO_RIGHTS(self, *args, **kwargs):
        raise web.notfound("You do not have the rights to view this page.")

    def required_role(self, method="POST"):
        """ Allow to override the minimal access right needed for this page. Method can be either "POST" or "GET" """
        return self.learner_role

    def verify_role(self, roles, method):
        for role in self.required_role(method):
            if role in roles:
                return True
        return False

    def POST(self, session_identifier, *args, **kwargs):
        self.user_manager.set_session_identifier(session_identifier)
        try:
            self._verify_lti_status("POST")
        except LTINotConnectedException:
            return self.LTI_POST_NOT_CONNECTED(*args, **kwargs)
        except LTINoRightsException:
            return self.LTI_POST_NO_RIGHTS(*args, **kwargs)
        except Exception as e:
            raise web.notfound(str(e))
        return self.LTI_POST(*args, **kwargs)

    def GET(self, session_identifier, *args, **kwargs):
        self.user_manager.set_session_identifier(session_identifier)
        try:
            self._verify_lti_status("GET")
        except LTINotConnectedException:
            return self.LTI_GET_NOT_CONNECTED(*args, **kwargs)
        except LTINoRightsException:
            return self.LTI_GET_NO_RIGHTS(*args, **kwargs)
        except Exception as e:
            raise web.notfound(str(e))
        return self.LTI_GET(*args, **kwargs)

    def _verify_lti_status(self, method="POST"):
        """ Verify session and/or parse the LTI data from the POST request """

        if not self.user_manager.session_logged_in():
            raise LTINotConnectedException()

        if not self.verify_role(self.user_manager.session_roles(), method):
            raise LTINoRightsException()

        try:
            course_id, task_id = self.user_manager.session_task()
            self.course = self.course_factory.get_course(course_id)
            self.task = self.course.get_task(task_id)
        except:
            raise LTINotConnectedException()


class LTILaunchPage(LTIPage, metaclass=abc.ABCMeta):
    """
    Page called by the TC to start an INGInious session
    """
    def POST(self, courseid, taskid, *args, **kwargs):
        try:
            self._parse_lti_data(courseid, taskid)
        except Exception as e:
            raise web.notfound(str(e))
        return self.LAUNCH_POST(*args, **kwargs)

    @abc.abstractmethod
    def LAUNCH_POST(self):
        pass

    def _parse_lti_data(self, courseid, taskid):
        """ Verify and parse the data for the LTI basic launch """
        post_input = web.webapi.rawinput("POST")
        try:
            verified = verify_request_common(self.consumers, web.ctx.home + web.ctx.fullpath, "POST", {}, post_input)
        except:
            raise Exception("Cannot authentify request (1)")

        if verified:
            user_id = post_input["user_id"]
            roles = post_input.get("roles", "Student").split(",")
            realname = self._find_realname(post_input)
            email = post_input.get("lis_person_contact_email_primary", "")
            lis_outcome_service_url = post_input.get("lis_outcome_service_url", None)
            outcome_result_id = post_input.get("lis_result_sourcedid", None)
            consumer_key = post_input["oauth_consumer_key"]

            if lis_outcome_service_url is None:
                raise Exception("INGInious needs the parameter lis_outcome_service_url in the LTI basic-launch-request")
            if outcome_result_id is None:
                raise Exception("INGInious needs the parameter lis_result_sourcedid in the LTI basic-launch-request")

            self.user_manager.lti_auth(user_id, roles, realname, email, courseid, taskid, consumer_key, lis_outcome_service_url, outcome_result_id)
        else:
            raise Exception("Cannot authentify request (2)")

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
