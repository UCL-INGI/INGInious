# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some utils for all the pages """
import abc
import hashlib

from pylti.common import verify_request_common
import web
import logging


class LTIPage(object):
    """
    A base for all the pages of the INGInious LTI tool provider.
    Contains references to the PluginManager, the CourseFactory, and the SubmissionManager
    """

    def __init__(self, plugin_manager, course_factory, task_factory, submission_manager, user_manager, template_helper, database,
                 gridfs, default_allowed_file_extensions, default_max_file_size, containers, consumers):
        """
        Init the page
        :type plugin_manager: inginious.frontend.common.plugin_manager.PluginManager
        :type course_factory: inginious.common.course_factory.CourseFactory
        :type task_factory: inginious.common.task_factory.TaskFactory
        :type submission_manager: inginious.frontend.common.submission_manager.SubmissionManager
        :type user_manager: inginious.frontend.lti.user_manager.UserManager
        :type template_helper: inginious.frontend.common.template_helper.TemplateHelper
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
        self.consumers = consumers
        self.logger = logging.getLogger('lti.pages.utils')

class LTINotConnectedException(Exception):
    pass
class LTINoRightsException(Exception):
    pass

class LTIAuthenticatedPage(LTIPage):
    """ A page that needs to be authentified by the TC """

    admin_role = ("Instructor", "Staff", "Administrator")
    tutor_role = ("Mentor",) + admin_role
    learner_role = ("Student", "Learner", "Member") + tutor_role

    def __init__(self, plugin_manager, course_factory, task_factory, submission_manager, user_manager, template_helper, database,
                 gridfs, default_allowed_file_extensions, default_max_file_size, containers, consumers):
        super(LTIAuthenticatedPage, self).__init__(plugin_manager, course_factory, task_factory, submission_manager, user_manager, template_helper,
                                                   database,
                                                   gridfs, default_allowed_file_extensions, default_max_file_size, containers, consumers)
        self.course = None
        self.task = None

    def LTI_POST(self, *args, **kwargs):
        raise web.notacceptable()

    def LTI_GET(self, *args, **kwargs):
        raise web.notacceptable()

    def LTI_GET_NOT_CONNECTED(self, *args, **kwargs):
        self.logger.info('ERROR: LTI_GET_NOT_CONNECTED')
        raise web.notfound("Your session expired. Please reload the page.")

    def LTI_POST_NOT_CONNECTED(self, *args, **kwargs):
        self.logger.info('ERROR: LTI_POST_NOT_CONNECTED')
        raise web.notfound("Your session expired. Please reload the page.")

    def LTI_GET_NO_RIGHTS(self, *args, **kwargs):
        self.logger.info('ERROR: LTI_GET_NO_RIGHTS')
        raise web.notfound("You do not have the rights to view this page.")

    def LTI_POST_NO_RIGHTS(self, *args, **kwargs):
        self.logger.info('ERROR: LTI_POST_NOT_CONNECTED')
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
            self.logger.debug('ERROR: POST ' + str(e))
            raise
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
            self.logger.debug('ERROR: GET ' + str(e))
            raise
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

class LTILaunchPage(LTIPage):
    __metaclass__ = abc.ABCMeta

    def __init__(self, plugin_manager, course_factory, task_factory, submission_manager, user_manager, template_helper, database,
                 gridfs, default_allowed_file_extensions, default_max_file_size, containers, consumers):
        super(LTILaunchPage, self).__init__(plugin_manager, course_factory, task_factory, submission_manager, user_manager, template_helper, database,
                                            gridfs, default_allowed_file_extensions, default_max_file_size, containers, consumers)

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
        self.logger.debug('_parse_lti_data:'  + str(post_input))
        try:
            verified = verify_request_common(self.consumers, web.ctx.home + web.ctx.fullpath, "POST", {}, post_input)
        except Exception as e:
            self.logger.info('Can not authenticate request for ' + str(post_input))
            raise Exception("Cannot authentify request (1)")

        if verified:
            self.logger.debug('parse_lit_data for ' + str(post_input))
            user_id = post_input["user_id"]
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

            self.user_manager.lti_auth(user_id, roles, realname, email, courseid, taskid,
                                       consumer_key, lis_outcome_service_url, outcome_result_id)
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
