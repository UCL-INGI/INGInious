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
""" Plugin Manager """
import importlib

from backend.hook_manager import HookManager
from common.singleton import Singleton
import common_frontend.templates


class PluginManager(HookManager):
    """ Registers an manage plugins. Singleton class. """

    __metaclass__ = Singleton

    def __init__(self, webpy_app=None, course_factory=None, task_factory = None, config=None):
        if webpy_app is None or course_factory is None or task_factory is None or config is None:
            raise Exception("Plugin Manager should be initialized before call")

        HookManager.__init__(self)
        self.app = webpy_app
        self.plugins = []
        self.authentication = []
        self._config = config
        self._course_factory = course_factory
        self._task_factory = task_factory

        common_frontend.templates.add_to_template_globals("PluginManager", self)

    def load(self, job_manager):
        """ Loads the plugin manager. Must be done after the initialisation of the job_manager """
        for entry in self._config:
            module = importlib.import_module(entry["plugin_module"])
            self.plugins.append(module.init(self, self._course_factory, job_manager, entry))

    def add_page(self, pattern, classname):
        """ Add a new page to the web application """
        self.app.add_mapping(pattern, classname)

    def add_task_file_manager(self, task_file_manager):
        """ Add a task file manager """
        self._task_factory.add_custom_task_file_manager(task_file_manager)

    def register_auth_method(self, name, input_to_display, callback):
        """
            Register a new authentication method

            name
                the name of the authentication method, typically displayed by the webapp

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
