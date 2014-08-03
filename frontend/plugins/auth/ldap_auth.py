# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" LDAP plugin """

import simpleldap
import frontend.user


def init(plugin_manager, conf):
    """
        Allow to connect through a LDAP service

        Available configuration:
        ::

            {
                "plugin_module": "frontend.plugins.auth.ldap_auth",
                "host": "ldap.test.be",
                "port": 0,
                "encryption": "ssl",
                "base_dn": "o=test,c=be",
                "request": "uid={}",
                "prefix": "",
                "name": "LDAP Login",
                "require_cert": true
            }

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

    def connect(login_data):
        """ Connect throught LDAP """
        try:
            # Get configuration
            login = login_data["login"]
            password = login_data["password"]

            encryption = conf.get('encryption', "none")
            if encryption not in ["none", "ssl", "tls"]:
                raise Exception("Unknown encryption method {}".format(encryption))
            if encryption == "none":
                encryption = None

            host = conf.get('host', "ldap.test.be")
            port = conf.get('port', 0)
            if port == 0:
                port = None

            base_dn = conf.get('base_dn', '')

            require_cert = conf.get('require_cert', True)

            # Connect to the ldap
            conn = simpleldap.Connection(host, port=port, encryption=encryption, require_cert=require_cert, search_defaults={"base_dn": base_dn})
            request = conf.get('request', "uid={},ou=People").format(login)
            user_data = conn.get(request)
            if conn.authenticate(user_data.dn, password):
                email = user_data["mail"][0]
                username = conf.get('prefix', '') + user_data["uid"][0]
                realname = user_data["cn"][0]

                frontend.user.connect_user_internal(username, email, realname)
                return True
            else:
                return False
        except:
            return False

    plugin_manager.register_auth_method(conf.get('name', 'LDAP Login'), {"login": {"type": "text", "placeholder": "Login"}, "password": {"type": "password", "placeholder": "Password"}}, connect)
