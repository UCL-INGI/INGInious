# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

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
        self._database = None
        self._user_manager = None
        self._submission_manager = None

    def load(self, client, webpy_app, course_factory, task_factory, database, user_manager, submission_manager, config):
        """ Loads the plugin manager. Must be done after the initialisation of the client """
        self._app = webpy_app
        self._task_factory = task_factory
        self._database = database
        self._user_manager = user_manager
        self._submission_manager = submission_manager
        self._loaded = True
        for entry in config:
            module = importlib.import_module(entry["plugin_module"])
            module.init(self, course_factory, client, entry)

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

    def get_database(self):
        """ Returns the frontend database"""
        return self._database

    def get_submission_manager(self):
        """ Returns the submission manager"""
        return self._submission_manager

    def get_user_manager(self):
        """ Returns the user manager"""
        return self._user_manager
