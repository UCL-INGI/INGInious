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

    @staticmethod
    def _ldap_request(login, password, host, port=None, encryption=None, bind_dn=None, bind_password=None,
                      bind_password_file=None, base_dn=None, request=None, start_tls='NONE', cn='cn', mail='mail',
                      **__unused_kwargs):
        # Define ldap server object
        server = ldap3.Server(host, port=port, use_ssl=encryption == 'ssl', get_info=ldap3.ALL)

        # auto_bind can be NONE, NO_TLS, TLS_AFTER_BIND, TLS_BEFORE_BIND
        if start_tls == 'NO_TLS':
            auto_bind = ldap3.AUTO_BIND_NO_TLS
        elif start_tls == 'TLS_AFTER_BIND':
            auto_bind = ldap3.AUTO_BIND_TLS_AFTER_BIND
        elif start_tls == 'TLS_BEFORE_BIND':
            auto_bind = ldap3.AUTO_BIND_TLS_BEFORE_BIND
        else:
            auto_bind = ldap3.AUTO_BIND_NONE

        # If bind_dn is used, try to get the configured password
        # 1. bind_password
        # 2. First line from file bind_password_file
        # 3. Password provided by the user from the website
        if bind_dn:
            if bind_password is None:
                if bind_password_file is None:
                    bind_password = password
                else:
                    try:
                        with open(bind_password_file, 'r') as file:
                            bind_password = file.readline().strip()
                    except FileNotFoundError:
                        raise Exception('Invalid configuration: Password file not found')
                    except PermissionError:
                        raise Exception('Invalid configuration: Insufficient permissions on password file')

        # Connect to the server
        # With auto bind:
        #   Bind (Log in) to a specific user to query ldap and afterward check the password
        # Without auto bind:
        #   Query anonymously the user data and check the password (anonymously querying is not always possible)
        try:
            logger.debug('Connecting to {}, port {} (SSL={})'.format(host, port, encryption == 'ssl'))
            if bind_dn:
                # Connect with auto bind
                bind_dn = bind_dn.format(login)
                conn = ldap3.Connection(server, auto_bind=auto_bind, user=bind_dn, password=bind_password)
            else:
                # Connect normally
                conn = ldap3.Connection(server, auto_bind=auto_bind)
        except Exception as e:
            logger.error('Unable to connect to {}, port {} (SSL={}): {}'.format(host, port, encryption == 'ssl',
                                                                                str(e)))
            if type(e) == ldap3.core.exceptions.LDAPBindError:
                raise Exception('Invalid credentials')
            else:
                raise Exception('Unable to contact ldap server')

        # Request configured 'cn' and 'mail' from the server
        try:
            request = request.format(login)
            conn.search(base_dn, request, attributes=[cn, mail])
            user_data = conn.response[0]
        except ldap3.core.exceptions.LDAPSocketOpenError as e:
            logger.error('Unable to contact host: {} ({})'.format(str(e), host))
            conn.unbind()
            raise Exception('Unable to contact host')
        except Exception as e:
            logger.error('Unable to get user data: {}'.format(str(e)))
            conn.unbind()
            raise Exception('Unknown User')

        # 'Log in' (bind) to the ldap connection
        if conn.rebind(user_data['dn'], password=password):
            try:
                email = user_data['attributes'][mail]
                username = login
                realname = user_data['attributes'][cn]

                logger.debug('Successfully fetched data from ldap for user {}'.format(login))

                return email, username, realname
            except KeyError as e:
                logger.error('Unable to fetch attribute "{}"'.format(str(e)))
                raise Exception('Unable to fetch attribute "{}"'.format(str(e)))
            except Exception as e:
                logger.error('Unable to fetch some attributes: {}'.format(str(e)))
                raise Exception('Unable to fetch some attributes')
            finally:
                conn.unbind()
        else:
            logger.error('Unable to authenticate user')
            conn.unbind()
            raise Exception('Unable to authenticate user')

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
            email, username, realname = self._ldap_request(login, password, **settings)
        except Exception as e:
            return self.template_helper.get_custom_renderer('frontend/plugins/auth').custom_auth_form(settings,
                                                                                                      str(e))
        if not email or not username or not realname:
            # Unknown Auth Error
            return self.template_helper.get_custom_renderer('frontend/plugins/auth').custom_auth_form(settings,
                                                                                                      'Unknown error')

        self.user_manager.bind_user(id, (username, realname, email))
        auth_storage = self.user_manager.session_auth_storage().setdefault(id, {})
        raise web.seeother(auth_storage.get("redir_url", "/"))


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
