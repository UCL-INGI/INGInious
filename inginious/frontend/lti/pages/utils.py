# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some utils for all the pages """
import abc
from typing import List, Dict

from gridfs import GridFS
# from pylti.common import verify_request_common TODO re-add me once PR has been accepted by PyLTI devs
from inginious.common.customlibs.pylti import verify_request_common
import web
import logging

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
        """ Returns the web application singleton """
        return web.ctx.app_stack[0]

    @property
    def plugin_manager(self) -> PluginManager:
        """ Returns the plugin manager singleton """
        return self.app.plugin_manager

    @property
    def course_factory(self) -> CourseFactory:
        """ Returns the course factory singleton """
        return self.app.course_factory

    @property
    def task_factory(self) -> TaskFactory:
        """ Returns the task factory singleton """
        return self.app.task_factory

    @property
    def submission_manager(self) -> SubmissionManager:
        """ Returns the submission manager singleton"""
        return self.app.submission_manager

    @property
    def user_manager(self) -> UserManager:
        """ Returns the user manager singleton """
        return self.app.user_manager

    @property
    def template_helper(self) -> TemplateHelper:
        """ Returns the Template Helper singleton """
        return self.app.template_helper

    @property
    def database(self) -> Database:
        """ Returns the database singleton """
        return self.app.database

    @property
    def gridfs(self) -> GridFS:
        """ Returns the GridFS singleton """
        return self.app.gridfs

    @property
    def default_allowed_file_extensions(self) -> List[str]:  # pylint: disable=invalid-sequence-index
        """ List of allowed file extensions """
        return self.app.default_allowed_file_extensions

    @property
    def default_max_file_size(self) -> int:
        """ Default maximum file size for upload """
        return self.app.default_max_file_size

    @property
    def containers(self) -> List[str]:  # pylint: disable=invalid-sequence-index
        """ Available containers """
        return self.app.submission_manager.get_available_environments()

    @property
    def consumers(self) -> Dict[str, Dict[str, str]]:
        """ Consumers keys """
        return self.app.consumers

    @property
    def logger(self) -> logging.Logger:
        """ Logger """
        return logging.getLogger('inginious.lti.pages.utils')

    @property
    def webterm_link(self) -> str:
        """ Returns the link to the web terminal """
        return self.app.webterm_link


class LTINotConnectedException(Exception):
    """
    Exception risen when user is not authenticated
    """
    pass


class LTINoRightsException(Exception):
    """
    Exception risen when the page cannot be seen by current user
    """
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

    def LTI_POST(self, *args, **kwargs):  # pylint: disable=unused-argument
        raise web.notacceptable()

    def LTI_GET(self, *args, **kwargs):  # pylint: disable=unused-argument
        raise web.notacceptable()

    def LTI_GET_NOT_CONNECTED(self, *args, **kwargs):  # pylint: disable=unused-argument
        self.logger.info('ERROR: LTI_GET_NOT_CONNECTED')
        raise web.notfound("Your session expired. Please reload the page.")

    def LTI_POST_NOT_CONNECTED(self, *args, **kwargs):  # pylint: disable=unused-argument
        self.logger.info('ERROR: LTI_POST_NOT_CONNECTED')
        raise web.notfound("Your session expired. Please reload the page.")

    def required_role(self, method="POST"):  # pylint: disable=unused-argument
        """ Allow to override the minimal access right needed for this page. Method can be either "POST" or "GET" """
        return self.learner_role

    def verify_role(self, roles, method):
        """ Check if"""
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
            self.logger.info('ERROR: LTI_POST_NOT_CONNECTED')
            raise web.notfound("You do not have the rights to view this page.")
        except Exception as e:
            self.logger.debug('ERROR: POST ' + str(e))
            raise web.notfound(str(e))
        return self.LTI_POST(*args, **kwargs)

    def GET(self, session_identifier, *args, **kwargs):
        self.user_manager.set_session_identifier(session_identifier)
        try:
            self._verify_lti_status("GET")
        except LTINotConnectedException:
            return self.LTI_GET_NOT_CONNECTED(*args, **kwargs)
        except LTINoRightsException:
            self.logger.info('ERROR: LTI_GET_NO_RIGHTS')
            raise web.notfound("You do not have the rights to view this page.")
        except Exception as e:
            self.logger.debug('ERROR: GET ' + str(e))
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
        except:
            raise LTINotConnectedException()

        try:
            self.course = self.course_factory.get_course(course_id)
            self.task = self.course.get_task(task_id)
        except:
            raise web.notfound()


class LTILaunchPage(LTIPage, metaclass=abc.ABCMeta):
    """
    Page called by the TC to start an INGInious session
    """
    def POST(self, courseid, taskid, *args, **kwargs):
        try:
            self._parse_lti_data(courseid, taskid)
        except Exception as e:
            self.logger.info('ERROR: POST exception ' + str(e))
            raise web.notfound(str(e))
        return self.LAUNCH_POST(*args, **kwargs)

    @abc.abstractmethod
    def LAUNCH_POST(self):
        pass

    def _parse_lti_data(self, courseid, taskid):
        """ Verify and parse the data for the LTI basic launch """
        post_input = web.webapi.rawinput("POST")
        self.logger.debug('_parse_lti_data:' + str(post_input))

        # Parse consumer list and keep allowed consumers for the course
        authorized_consumers = dict([(key, consumer) for key, consumer in self.consumers.items() if
                                     courseid in consumer.get("courses", courseid)])
        try:
            verified = verify_request_common(authorized_consumers, web.ctx.home + web.ctx.fullpath, "POST", {}, post_input)
        except Exception:
            self.logger.info('Can not authenticate request for %s', str(post_input))
            raise Exception("Cannot authentify request (1)")

        if verified:
            self.logger.debug('parse_lit_data for %s', str(post_input))
            user_id = post_input["user_id"]
            if 'ext_user_username' in post_input:
                ext_user_username = post_input['ext_user_username']
            else:
                ext_user_username = user_id
            roles = post_input.get("roles", "Student").split(",")
            realname = self._find_realname(post_input)
            email = post_input.get("lis_person_contact_email_primary", "")
            lis_outcome_service_url = post_input.get("lis_outcome_service_url", None)
            outcome_result_id = post_input.get("lis_result_sourcedid", None)
            consumer_key = post_input["oauth_consumer_key"]

            if lis_outcome_service_url is None:
                self.logger.info('Error: lis_outcome_service_url is None')
                raise Exception("INGInious needs the parameter lis_outcome_service_url in the LTI basic-launch-request")
            if outcome_result_id is None:
                self.logger.info('Error: lis_outcome_result_id is None')
                raise Exception("INGInious needs the parameter lis_result_sourcedid in the LTI basic-launch-request")

            self.user_manager.lti_auth(user_id, roles, realname, email, courseid, taskid, consumer_key, lis_outcome_service_url, outcome_result_id, ext_user_username)
        else:
            self.logger.info('ERROR: not verified')
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
