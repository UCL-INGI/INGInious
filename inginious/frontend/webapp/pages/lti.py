# coding=utf-8

import web
from inginious.common import exceptions
from inginious.frontend.webapp.lti_request_validator import LTIValidator
from inginious.frontend.webapp.lti_tool_provider import LTIWebPyToolProvider
from inginious.frontend.webapp.pages.tasks import BaseTaskPage
from inginious.frontend.webapp.pages.utils import INGIniousPage, INGIniousAuthPage


class LTITaskPage(INGIniousAuthPage):
    def is_lti_page(self):
        return True

    def GET_AUTH(self):
        data = self.user_manager.session_lti_info()
        if data is None:
            raise web.notfound()
        (courseid, taskid) = data['task']

        return BaseTaskPage(self).GET_AUTH(courseid, taskid, True)

    def POST_AUTH(self):
        data = self.user_manager.session_lti_info()
        if data is None:
            raise web.notfound()
        (courseid, taskid) = data['task']

        return BaseTaskPage(self).POST_AUTH(courseid, taskid, True)

class LTILaunchPage(INGIniousPage):
    """
    Page called by the TC to start an LTI session on a given task
    """

    def POST(self, courseid, taskid):
        (sessionid, loggedin) = self._parse_lti_data(courseid, taskid)

        if loggedin:
            raise web.seeother(self.app.get_homepath() + "/lti/task")
        else:
            raise web.seeother(self.app.get_homepath() + "/lti/login")

    def _parse_lti_data(self, courseid, taskid):
        """ Verify and parse the data for the LTI basic launch """
        post_input = web.webapi.rawinput("POST")
        self.logger.debug('_parse_lti_data:' + str(post_input))

        try:
            course = self.course_factory.get_course(courseid)
        except exceptions.CourseNotFoundException as ex:
            raise web.notfound(str(ex))

        try:
            test = LTIWebPyToolProvider.from_webpy_request()
            validator = LTIValidator(self.database.nonce, course.lti_keys())
            verified = test.is_valid_request(validator)
        except Exception:
            self.logger.exception("...")
            self.logger.info('Can not authenticate request for %s', str(post_input))
            raise web.forbidden('Cannot authenticate request (1)')

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
                raise web.forbidden("INGInious needs the parameter lis_outcome_service_url in the LTI basic-launch-request")
            if outcome_result_id is None:
                self.logger.info('Error: lis_outcome_result_id is None')
                raise web.forbidden("INGInious needs the parameter lis_result_sourcedid in the LTI basic-launch-request")

            session_id = self.user_manager.create_lti_session(user_id, roles, realname, email, courseid, taskid, consumer_key,
                                                              lis_outcome_service_url, outcome_result_id, ext_user_username)
            loggedin = self.user_manager.attempt_lti_login()

            return session_id, loggedin
        else:
            self.logger.info('ERROR: not verified')
            raise web.forbidden("Cannot authentify request (2)")

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
