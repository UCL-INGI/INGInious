# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" SAML SSO plugin """

import web
import logging
import copy

from inginious.frontend.webapp.pages.utils import INGIniousPage
from inginious.frontend.webapp.user_manager import AuthMethod
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

settings = None


class SAMLAuthMethod(AuthMethod):
    """
    SAML SSO auth method
    """

    def __init__(self, name, settings):
        self._name = name
        self._settings = settings

    def get_name(self):
        return self._name

    def auth(self, login_data):
        auth = OneLogin_Saml2_Auth(prepare_request(), settings)
        raise web.seeother(auth.login(web.ctx.path + web.ctx.query.rsplit("?logoff")[0]))

    def needed_fields(self):
        return {
            "input": {},
            "info": ''
        }

    def should_cache(self):
        """ SAML-SSO always put connected people in cache at login-time"""
        return True

    def get_users_info(self, usernames):
        """
        SAML SSO does not enable searching for user data, it relies on the cache !
        :param usernames: a list of usernames
        :return: a dict containing key/pairs {username: None}
        """
        return {username: None for username in usernames}


def prepare_request():
    """ Prepare SAML request """

    # Set the ACS url and binding method
    settings["sp"]["assertionConsumerService"] = {
        "url": web.ctx.homedomain + web.ctx.homepath + "/SAML/ACS",
        "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
    }

    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    data = web.input()
    return {
        'https': 'on' if web.ctx.protocol == 'https' else 'off',
        'http_host': web.ctx.environ["SERVER_NAME"],
        'server_port': web.ctx.environ["SERVER_PORT"],
        'script_name': web.ctx.homepath,
        'get_data': data.copy(),
        'post_data': data.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'query_string': web.ctx.query
    }


class MetadataPage:
    def GET(self):
        global settings
        auth = OneLogin_Saml2_Auth(prepare_request(), settings)
        metadata = auth.get_settings().get_sp_metadata()
        errors = auth.get_settings().validate_metadata(metadata)

        if len(errors) == 0:
            web.header('Content-Type', 'text/xml')
            return metadata
        else:
            web.ctx.status = "500 Internal Server Error"
            return ', '.join(errors)


class SAMLPage(INGIniousPage):
    def POST(self):
        req = prepare_request()
        input_data = web.input()

        auth = OneLogin_Saml2_Auth(req, settings)
        auth.process_response()
        errors = auth.get_errors()

        # Try and check if IdP is using several signature certificates
        # This is a limitation of python3-saml
        for cert in settings["idp"].get("additionalX509certs", []):
            if auth.get_last_error_reason() == "Signature validation failed. SAML Response rejected":
                # Change used IdP certificate
                logging.getLogger('inginious.webapp.plugin.auth.saml').debug("Trying another certificate...")
                new_settings = copy.deepcopy(settings)
                new_settings["idp"]["x509cert"] = cert
                # Retry processing response
                auth = OneLogin_Saml2_Auth(req, new_settings)
                auth.process_response()
                errors = auth.get_errors()

        if len(errors) == 0 and "attributes" in settings:
            attrs = auth.get_attributes()

            username = attrs[settings["attributes"]["uid"]][0]
            realname = attrs[settings["attributes"]["cn"]][0]
            email = attrs[settings["attributes"]["email"]][0]

            # Initialize session in user manager and update cache
            self.user_manager._set_session(username, realname, email)
            self.database.user_info_cache.update_one({"_id": username}, {"$set": {"realname": realname, "email": email}}, upsert=True)
            self.user_manager._logger.info("User %s connected - %s - %s - %s", username, realname, email, web.ctx.ip)

            # Redirect to desired url
            self_url = OneLogin_Saml2_Utils.get_self_url(req)
            if 'RelayState' in input_data and self_url != input_data['RelayState']:
                raise web.seeother(auth.redirect_to(input_data['RelayState']))
        else:
            logging.getLogger('inginious.webapp.plugin.auth.saml').error("Errors while processing response : " + ", ".join(errors))
            raise web.seeother("/")


def init(plugin_manager, course_factory, client, conf):
    global settings
    settings = conf
    plugin_manager.add_page('/SAML/Metadata', MetadataPage)
    plugin_manager.add_page('/SAML/ACS', SAMLPage)
    plugin_manager.register_auth_method(SAMLAuthMethod(conf.get('name', 'SAML Login'), settings))
