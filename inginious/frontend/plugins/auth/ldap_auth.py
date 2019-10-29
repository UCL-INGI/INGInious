# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" LDAP plugin """

import logging

import ldap3
import web

from inginious.frontend.pages.social import AuthenticationPage
from inginious.frontend.user_manager import AuthMethod

logger = logging.getLogger('inginious.webapp.plugin.auth.ldap')


class LdapAuthMethod(AuthMethod):
    """
    LDAP auth method
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
                   'user-select: none; max-height:50px;" />'
        else:
            return '<i class="fa fa-address-book" style="font-size:50px; color:#000000;"></i>'

    def get_auth_link(self, auth_storage, share=False):
        return "/auth/page/" + self._id

    def callback(self, auth_storage):
        return None

    def share(self, auth_storage, course, task, submission, language):
        return False

    def allow_share(self):
        return False

    def get_settings(self):
        return self._settings


class LDAPAuthenticationPage(AuthenticationPage):
    def GET(self, id):
        settings = self.user_manager.get_auth_method(id).get_settings()
        return self.template_helper.get_custom_renderer('frontend/plugins/auth').custom_auth_form(settings,
                                                                                                         False)

    def POST(self, id):
        # Get configuration
        settings = self.user_manager.get_auth_method(id).get_settings()
        login_data = web.input()
        login = login_data["login"].strip().lower()
        password = login_data["password"]

        # do not send empty password to the LDAP
        if password.rstrip() == "":
            return self.template_helper.get_custom_renderer('frontend/plugins/auth').custom_auth_form(
                settings, "Empty password")

        try:
            # Connect to the ldap
            logger.debug('Connecting to ' + settings['host'] + ", port " + str(settings['port']))
            conn = ldap3.Connection(
                ldap3.Server(settings['host'], port=settings['port'], use_ssl=settings["encryption"] == 'ssl',
                             get_info=ldap3.ALL), auto_bind=True)
            logger.debug('Connected to ' + settings['host'] + ", port " + str(settings['port']))
        except Exception as e:
            logger.exception("Can't initialze connection to " + settings['host'] + ': ' + str(e))
            return self.template_helper.get_custom_renderer('frontend/plugins/auth').custom_auth_form(
                settings, "Cannot contact host")

        try:
            request = settings["request"].format(login)
            conn.search(settings["base_dn"], request, attributes=["cn", "mail"])
            user_data = conn.response[0]
        except Exception as ex:
            logger.exception("Can't get user data : " + str(ex))
            conn.unbind()
            return self.template_helper.get_custom_renderer('frontend/plugins/auth').custom_auth_form(
                settings, "Unknown user")

        if conn.rebind(user_data['dn'], password=password):
            try:
                email = user_data["attributes"][settings.get("mail", "mail")][0]
                username = login
                realname = user_data["attributes"][settings.get("cn", "cn")][0]
            except KeyError as e:
                logger.exception("Can't get field " + str(e) + " from your LDAP server")
                return self.template_helper.get_custom_renderer('frontend/plugins/auth').custom_auth_form(
                    settings, "Can't get field " + str(e) + " from your LDAP server")
            except Exception as e:
                logger.exception("Can't get some user fields")
                return self.template_helper.get_custom_renderer('frontend/plugins/auth').custom_auth_form(
                settings, "Can't get some user fields")

            conn.unbind()

            self.user_manager.bind_user(id, (username, realname, email, {}))
            
            auth_storage = self.user_manager.session_auth_storage().setdefault(id, {})
            raise web.seeother(auth_storage.get("redir_url", "/"))
        else:
            logger.debug('Auth Failed')
            conn.unbind()
            return self.template_helper.get_custom_renderer('frontend/plugins/auth').custom_auth_form(
                settings, "Incorrect password")


def init(plugin_manager, _, _2, conf):
    """
        Allow to connect through a LDAP service

        Available configuration:
        ::

            plugins:
                - plugin_module": "inginious.frontend.plugins.auth.ldap_auth",

                  host: "ldap.test.be",
                  port: 0,
                  encryption: "ssl",
                  base_dn: "o=test,c=be",
                  request: "(uid={})",
                  name: "LDAP Login"

        *host*
            The host of the ldap server
        *encryption*
            Encryption method used to connect to the LDAP server
            Can be either "none", "ssl" or "tls"
        *request*
            Request made to the server in order to find the dn of the user. The characters "{}" will be replaced by the login name.

    """

    encryption = conf.get("encryption", "none")
    if encryption not in ["none", "ssl", "tls"]:
        raise Exception("Unknown encryption method {}".format(encryption))
    if encryption == "none":
        conf["encryption"] = None

    if conf.get("port", 0) == 0:
        conf["port"] = None

    the_method = LdapAuthMethod(conf.get("id"), conf.get('name', 'LDAP'), conf.get("imlink", ""), conf)
    plugin_manager.add_page(r'/auth/page/([^/]+)', LDAPAuthenticationPage)
    plugin_manager.register_auth_method(the_method)
