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
""" Demo auth """

import frontend.user


def init(plugin_manager, conf):
    """
        A simple authentication that uses password stored in plain-text in the config.

        DO NOT USE IT IN PRODUCTION ENVIRONMENT!

        Available configuration:
        ::

            {
                "plugin_module": "frontend.plugins.auth.demo_auth",
                "users":
                {
                    "username1":"password1",
                    "username2":"password2"
                }
            }
    """

    def connect(login_data):
        """ Connect the user """
        login = login_data["login"]
        password = login_data["password"]

        if conf.get('users', {}).get(login) == password:
            frontend.user.connect_user_internal(login, "{}@inginious".format(login), login)
            return True
        else:
            return False

    plugin_manager.register_auth_method(conf.get('name', 'Demo'), {"login": {"type": "text", "placeholder": "Login"}, "password": {"type": "password", "placeholder": "Password"}}, connect)
