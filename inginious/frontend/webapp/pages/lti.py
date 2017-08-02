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


class LTIBindPage(INGIniousAuthPage):
    def is_lti_page(self):
        return False

    def fetch_lti_data(self, sessionid):
        cookieless_session = self.app.get_session().store[sessionid]
        data = cookieless_session["lti"]

        return cookieless_session, data

    def GET_AUTH(self):
        input_data = web.input()
        if "sessionid" not in input_data:
            return self.template_helper.get_renderer().lti_bind(False, "", None, "Missing LTI session id")

        try:
            cookieless_session, data = self.fetch_lti_data(input_data["sessionid"])
        except KeyError as _:
            return self.template_helper.get_renderer().lti_bind(False, "", None, "Invalid LTI session id")

        return self.template_helper.get_renderer().lti_bind(False, cookieless_session["session_id"], data, "")

    def POST_AUTH(self):
        input_data = web.input()
        if "sessionid" not in input_data:
            return self.template_helper.get_renderer().lti_bind(False, "", None, "Missing LTI session id")

        try:
            cookieless_session, data = self.fetch_lti_data(input_data["sessionid"])
        except KeyError as _:
            return self.template_helper.get_renderer().lti_bind(False, "", None, "Invalid LTI session id")

        try:
            course = self.course_factory.get_course(data["task"][0])
            if data["consumer_key"] not in course.lti_keys().keys():
                raise Exception()
        except:
            return self.template_helper.get_renderer().lti_bind(False, "", None, "Invalid LTI data")

        if data:
            user_profile = self.database.users.find_one({"username": self.user_manager.session_username()})
            lti_user_profile = self.database.users.find_one(
                {"ltibindings." + data["task"][0] + "." + data["consumer_key"]: data["username"]})
            if not user_profile.get("ltibindings", {}).get(data["task"][0], {}).get(data["consumer_key"],
                                                                                    "") and not lti_user_profile:
                # There is no binding yet, so bind LTI to this account
                self.database.users.find_one_and_update({"username": self.user_manager.session_username()}, {"$set": {
                    "ltibindings." + data["task"][0] + "." + data["consumer_key"]: data["username"]}})
            elif not (lti_user_profile and user_profile["username"] == lti_user_profile["username"]):
                # There exists an LTI binding for another account, refuse auth!
                self.logger.info("User %s tried to bind LTI user %s in for %s:%s, but %s is already bound.",
                                 user_profile["username"],
                                 data["username"],
                                 data["task"][0],
                                 data["consumer_key"],
                                 user_profile.get("ltibindings", {}).get(data["task"][0], {}).get(data["consumer_key"], ""))
                return self.template_helper.get_renderer().lti_bind(False, cookieless_session["data"]["session_id"],
                                                                    data, "Your account is already bound with this context.")

        return self.template_helper.get_renderer().lti_bind(True, cookieless_session["session_id"], data, "")


class LTILoginPage(INGIniousPage):
    def is_lti_page(self):
        return True

    def GET(self):
        """
            Checks if user is authenticated and calls POST_AUTH or performs login and calls GET_AUTH.
            Otherwise, returns the login template.
        """
        data = self.user_manager.session_lti_info()
        if data is None:
            raise web.notfound()

        try:
            course = self.course_factory.get_course(data["task"][0])
            if data["consumer_key"] not in course.lti_keys().keys():
                raise Exception()
        except:
            return self.template_helper.get_renderer().lti_bind(False, "", None, "Invalid LTI data")

        user_profile = self.database.users.find_one({"ltibindings." + data["task"][0] + "." + data["consumer_key"]: data["username"]})
        if user_profile:
            self.user_manager.connect_user(user_profile["username"], user_profile["realname"], user_profile["email"])

        if self.user_manager.session_logged_in():
            raise web.seeother(self.app.get_homepath() + "/lti/task")

        return self.template_helper.get_renderer().lti_login(False)

    def POST(self):
        """
        Checks if user is authenticated and calls POST_AUTH or performs login and calls GET_AUTH.
        Otherwise, returns the login template.
        """
        return self.GET()


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
            roles = post_input.get("roles", "Student").split(",")
            realname = self._find_realname(post_input)
            email = post_input.get("lis_person_contact_email_primary", "")
            lis_outcome_service_url = post_input.get("lis_outcome_service_url", None)
            outcome_result_id = post_input.get("lis_result_sourcedid", None)
            consumer_key = post_input["oauth_consumer_key"]

            if course.lti_send_back_grade():
                if lis_outcome_service_url is None or outcome_result_id is None:
                    self.logger.info('Error: lis_outcome_service_url is None but lti_send_back_grade is True')
                    raise web.forbidden("In order to send grade back to the TC, INGInious needs the parameters lis_outcome_service_url and "
                                        "lis_outcome_result_id in the LTI basic-launch-request. Please contact your administrator.")
            else:
                lis_outcome_service_url = None
                outcome_result_id = None

            tool_name = post_input.get('tool_consumer_instance_name', 'N/A')
            tool_desc = post_input.get('tool_consumer_instance_description', 'N/A')
            tool_url = post_input.get('tool_consumer_instance_url', 'N/A')
            context_title = post_input.get('context_title', 'N/A')
            context_label = post_input.get('context_label', 'N/A')

            session_id = self.user_manager.create_lti_session(user_id, roles, realname, email, courseid, taskid, consumer_key,
                                                              lis_outcome_service_url, outcome_result_id, tool_name, tool_desc, tool_url,
                                                              context_title, context_label)
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
