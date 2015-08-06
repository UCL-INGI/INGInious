# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
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
""" Demo auth """

from inginious.frontend.webapp.user_manager import AuthMethod


class DemoAuthMethod(AuthMethod):
    """
    An example auth method
    """

    def __init__(self, name, users):
        self._name = name
        self._users = users

    def get_name(self):
        return self._name

    def auth(self, login_data):
        login = login_data["login"]
        password = login_data["password"]

        if self._users.get(login) == password:
            return (login, login, "{}@inginious.org".format(login))
        else:
            return None

    def needed_input(self):
        return {"login": {"type": "text", "placeholder": "Login"}, "password": {"type": "password", "placeholder": "Password"}}

    def should_cache(self):
        return False

    def get_users_info(self, usernames):
        """
        :param usernames: a list of usernames
        :return: a dict containing key/pairs {username: (realname, email)} if the user is available with this auth method,
            {username: None} else
        """
        retval = {username: None for username in usernames}
        for username in retval:
            if username in self._users:
                retval[username] = (username, "{}@inginious.org".format(username))
        return retval


def init(plugin_manager, _, _2, conf):
    """
        A simple authentication that uses password stored in plain-text in the config.

        DO NOT USE IT IN PRODUCTION ENVIRONMENT!

        Available configuration:
        ::

            {
                "plugin_module": "webapp.plugins.auth.demo_auth",
                "users":
                {
                    "username1":"password1",
                    "username2":"password2"
                }
            }
    """

    plugin_manager.register_auth_method(DemoAuthMethod(conf.get('name', 'Demo'), conf.get('users', {})))
