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

    def __init__(self, id, name, imlink, settings):
        self._id = id
        self._name = name
        self._imlink = imlink
        self._settings = settings

    def get_id(self):
        return self._id

    def get_name(self):
        return self._name

    def get_imlink(self):
        if self._imlink:
            return '<img src="' + self._imlink + \
                   '" style="-moz-user-select: none; -webkit-user-select: none; ' \
                   'user-select: none; width: 50px; height:50px;" />'
        else:
            return '<i class="fa fa-id-card" style="font-size:50px; color:#000000;"></i>'

    def get_auth_link(self, user_manager):
        auth = OneLogin_Saml2_Auth(prepare_request(self._settings), self._settings)
        return auth.login(user_manager.session_redir_url())

    def callback(self, user_manager):
        req = prepare_request(self._settings)
        input_data = web.input()

        auth = OneLogin_Saml2_Auth(req, self._settings)
        auth.process_response()
        errors = auth.get_errors()

        # Try and check if IdP is using several signature certificates
        # This is a limitation of python3-saml
        for cert in self._settings["idp"].get("additionalX509certs", []):
            if auth.get_last_error_reason() == "Signature validation failed. SAML Response rejected":
                # Change used IdP certificate
                logging.getLogger('inginious.webapp.plugin.auth.saml').debug("Trying another certificate...")
                new_settings = copy.deepcopy(self._settings)
                new_settings["idp"]["x509cert"] = cert
                # Retry processing response
                auth = OneLogin_Saml2_Auth(req, new_settings)
                auth.process_response()
                errors = auth.get_errors()

        if len(errors) == 0 and "attributes" in self._settings:
            attrs = auth.get_attributes()
            username = attrs[self._settings["attributes"]["uid"]][0]
            realname = attrs[self._settings["attributes"]["cn"]][0]
            email = attrs[self._settings["attributes"]["email"]][0]

            # Redirect to desired url
            self_url = OneLogin_Saml2_Utils.get_self_url(req)
            if 'RelayState' in input_data and self_url != input_data['RelayState']:
                redirect_url = auth.redirect_to(input_data['RelayState'])
                # Initialize session in user manager and update cache
                return (str(username), realname, email) if redirect_url == user_manager.session_redir_url() else None
        else:
            logging.getLogger('inginious.webapp.plugin.auth.saml').error("Errors while processing response : ",
                                                                         ", ".join(errors))
            return None

    def get_settings(self):
        return self._settings


class AuthenticationPage(INGIniousPage):
     def GET(self):
        auth = OneLogin_Saml2_Auth(prepare_request(), settings)
        raise web.seeother(auth.login(web.ctx.env.get('HTTP_REFERER','/').rsplit("?logoff")[0]))


def prepare_request(settings):
    """ Prepare SAML request """

    # Set the ACS url and binding method
    settings["sp"]["assertionConsumerService"] = {
        "url": web.ctx.homedomain + web.ctx.homepath + "/auth/" + settings["id"] + "/callback",
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


class MetadataPage(INGIniousPage):
    def GET(self, id):
        settings = self.user_manager.get_auth_method(id).get_settings()
        auth = OneLogin_Saml2_Auth(prepare_request(settings), settings)
        metadata = auth.get_settings().get_sp_metadata()
        errors = auth.get_settings().validate_metadata(metadata)

        if len(errors) == 0:
            web.header('Content-Type', 'text/xml')
            return metadata
        else:
            web.ctx.status = "500 Internal Server Error"
            return ', '.join(errors)


def init(plugin_manager, course_factory, client, conf):
    plugin_manager.add_page(r'/auth/([^/]+)/metadata', MetadataPage)
    plugin_manager.register_auth_method(SAMLAuthMethod(conf.get("id"), conf.get('name', 'SAML Login'), conf.get('imlink', ''), conf))

