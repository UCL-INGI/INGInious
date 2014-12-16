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
""" Plugin Manager """
import importlib

from backend.hook_manager import HookManager
import frontend.base


class PluginManager(HookManager):

    """ Registers an manage plugins """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PluginManager, cls).__new__(
                cls, *args, **kwargs)
        else:
            raise Exception("You should not instanciate PluginManager more than once")
        return cls._instance

    def __init__(self, app, config):
        HookManager.__init__(self)
        self.app = app
        self.plugins = []
        self.authentication = []
        self._config = config

        frontend.base.add_to_template_globals("PluginManager", self)

    def load(self):
        """ Loads the plugin manager. Must be done after the initialisation of the backend """
        for entry in self._config:
            module = importlib.import_module(entry["plugin_module"])
            self.plugins.append(module.init(self, entry))

    @classmethod
    def get_instance(cls):
        """ get the instance of PluginManager """
        return cls._instance

    def add_page(self, pattern, classname):
        """ Add a new page to the web application """
        self.app.add_mapping(pattern, classname)

    def register_auth_method(self, name, input_to_display, callback):
        """
            Register a new authentication method

            name
                the name of the authentication method, typically displayed by the frontend

            input_to_display
                a dictionary containing as key the name of the input (in the HTML sense of name), and, as value,
                a dictionary containing two fields:

                placeholder
                    the placeholder for the input

                type
                    text or password
        """
        self.authentication.append({"name": name, "input": input_to_display, "callback": callback})

    def get_all_authentication_methods(self):
        """
            Return an array of dict containing the following key-value pairs:

            name
                The name of the authentication method

            input
                the inputs to be displayed, as described in the register_auth_method method

            callback
                the callback function

            The key of the dict in the array is the auth_method_id of this method
        """
        return self.authentication

    def get_auth_method_callback(self, auth_method_id):
        """ Returns the callback method of a auth type by it's id """
        return self.authentication[auth_method_id]["callback"]
