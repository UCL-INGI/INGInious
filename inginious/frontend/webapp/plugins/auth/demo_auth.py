# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Demo auth """
from collections import OrderedDict

from inginious.frontend.webapp.user_manager import AuthMethod


class DemoAuthMethod(AuthMethod):
    """
    An example auth method
    """

    def __init__(self, name, users, ):
        self._name = name
        self._users = users

    def get_name(self):
        return self._name

    def auth(self, login_data, callback):
        login = login_data["login"].strip()
        password = login_data["password"]

        if self._users.get(login) == password:
            callback((login, login, "{}@inginious.org".format(login)))
            return True
        else:
            return False

    def needed_fields(self):
        return {"input": OrderedDict((("login", {"type": "text", "placeholder": "Login"}), ("password", {"type": "password", "placeholder":
            "Password"}))), "info": ""}

def init(plugin_manager, _, _2, conf):
    """
        A simple authentication that uses password stored in plain-text in the config.

        DO NOT USE IT IN PRODUCTION ENVIRONMENT!

        Available configuration:
        ::

            plugins:
                - plugin_module": "inginious.frontend.webapp.plugins.auth.demo_auth
                  users:
                        username1: "password1",
                        username2: "password2"

    """

    plugin_manager.register_auth_method(DemoAuthMethod(conf.get('name', 'Demo'), conf.get('users', {})))
