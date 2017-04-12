# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" LDAP plugin """
from collections import OrderedDict

import ldap3
import logging
import web

from inginious.frontend.webapp.user_manager import AuthMethod
from inginious.frontend.webapp.pages.utils import INGIniousPage, INGIniousAuthPage

settings = {}
logger = logging.getLogger('inginious.webapp.plugin.auth.ldap')


class LdapAuthMethod(AuthMethod):
    """
    LDAP auth method
    """

    def __init__(self, name, link):
        self._name = name
        self._link = link

    def get_name(self):
        return self._name

    def get_link(self):
        return self._link


class AuthenticationPage(INGIniousPage):
    def GET(self):
        self.user_manager._session['redir_url'] = web.ctx.env.get('HTTP_REFERER', '/').rsplit("?logoff")[0]
        return """
        <html><body><form method="post"><input type="text" name="login"/>
        <input type="password" name="password"/><input type="submit" value="Submit"></form></body></html>"""

    def POST(self):
        # Get configuration
        login_data = web.input()
        login = login_data["login"].strip().lower()
        password = login_data["password"]

        # do not send empty password to the LDAP
        if password.rstrip() == "":
            return """<html><body>empty password</body></html>"""

        try:
            # Connect to the ldap
            logger.debug('Connecting to ' + settings['host'] + ", port " + str(settings['port']))
            conn = ldap3.Connection(ldap3.Server(settings['host'], port=settings['port'], use_ssl=settings["encryption"] == 'ssl',
                                                 get_info=ldap3.ALL), auto_bind=True)
            logger.debug('Connected to ' + settings['host'] + ", port " + str(settings['port']))
        except Exception as e:
            logger.exception("Can't initialze connection to " + settings['host'] + ': ' + str(e))
            return """<html><body>cannot contact host</body></html>"""


        try:
            request = settings["request"].format(login)
            conn.search(settings["base_dn"], request, attributes=["cn", "mail"])
            user_data = conn.response[0]
        except Exception as ex:
            logger.exception("Can't get user data : " + str(ex))
            conn.unbind()
            return """<html><body>user not found</body></html>"""

        redirect_url = "/"
        if conn.rebind(user_data['dn'], password=password):
            try:
                email = user_data["attributes"][settings.get("mail", "mail")][0]
                username = settings.get("prefix", "") + login
                realname = user_data["attributes"][settings.get("cn", "cn")][0]
                self.user_manager.end_auth((username, realname, email), web.ctx.ip)
                redirect_url = self.user_manager._session['redir_url']
            except KeyError as e:
                logger.error("Can't get field " + str(e) + " from your LDAP server")
            except Exception as e:
                logger.exception("Can't get some user fields")
        else:
            logger.debug('Auth Failed')
            conn.unbind()
            return """<html><body>authentication failed</body></html>"""

        conn.unbind()
        raise web.seeother(redirect_url)

def init(plugin_manager, _, _2, conf):
    """
        Allow to connect through a LDAP service

        Available configuration:
        ::

            plugins:
                - plugin_module": "webapp.plugins.auth.ldap_auth",
                  host: "ldap.test.be",
                  port: 0,
                  encryption: "ssl",
                  base_dn: "o=test,c=be",
                  request: "uid={}",
                  prefix: "",
                  name: "LDAP Login",
                  require_cert: true

        *host*
            The host of the ldap server
        *encryption*
            Encryption method used to connect to the LDAP server
            Can be either "none", "ssl" or "tls"
        *request*
            Request made to the server in order to find the dn of the user. The characters "{}" will be replaced by the login name.
        *prefix*
            The prefix used internally to distinguish user that have the same username on different login services
        *require_cert*
            true if a certificate is needed.
    """
    global settings
    settings = conf

    encryption = conf.get("encryption", "none")
    if encryption not in ["none", "ssl", "tls"]:
        raise Exception("Unknown encryption method {}".format(encryption))
    if encryption == "none":
        conf["encryption"] = None

    if conf.get("port", 0) == 0:
        conf["port"] = None

    plugin_manager.add_page('/auth/ldap', AuthenticationPage)
    plugin_manager.register_auth_method( LdapAuthMethod(conf.get('name', 'LDAP Login'), "/auth/ldap"))
