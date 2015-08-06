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

from inginious.common.hook_manager import HookManager


class PluginManagerNotLoadedException(Exception):
    pass


class PluginManager(HookManager):
    """ Registers an manage plugins. The init method inits only the Hook Manager; you have to call the method load() to start the plugins """

    def __init__(self):
        HookManager.__init__(self)
        self._loaded = False
        self._app = None
        self._task_factory = None
        self._user_manager = None

    def load(self, job_manager, webpy_app, course_factory, task_factory, user_manager, config):
        """ Loads the plugin manager. Must be done after the initialisation of the job_manager """
        self._app = webpy_app
        self._task_factory = task_factory
        self._user_manager = user_manager
        self._loaded = True
        for entry in config:
            module = importlib.import_module(entry["plugin_module"])
            module.init(self, course_factory, job_manager, entry)

    def add_page(self, pattern, classname):
        """ Add a new page to the web application. Only available after that the Plugin Manager is loaded """
        if not self._loaded:
            raise PluginManagerNotLoadedException()
        self._app.add_mapping(pattern, classname)

    def add_task_file_manager(self, task_file_manager):
        """ Add a task file manager. Only available after that the Plugin Manager is loaded """
        if not self._loaded:
            raise PluginManagerNotLoadedException()
        self._task_factory.add_custom_task_file_manager(task_file_manager)

    def register_auth_method(self, auth_method):
        """
            Register a new authentication method

            name
                the name of the authentication method, typically displayed by the webapp

            input_to_display

            Only available after that the Plugin Manager is loaded
        """
        if not self._loaded:
            raise PluginManagerNotLoadedException()
        self._user_manager.register_auth_method(auth_method)
