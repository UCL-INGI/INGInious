# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Hook Manager """
import logging


class HookManager(object):
    """ Registers an manages hooks. Hooks are callback functions called when the inginious.backend does a specific action. """

    def __init__(self):
        self.hooks = {}
        self._logger = logging.getLogger("inginious.common.hookmanager")

    def _exception_free_callback(self, callback, *args, **kwargs):
        """ A wrapper that remove all exceptions raised from hooks """
        try:
            return callback(*args, **kwargs)
        except Exception:
            self._logger.exception("An exception occurred while calling a hook! ",exc_info=True)
            return None

    def add_hook(self, name, callback):
        """ Add a new hook that can be called with the call_hook function """
        hook_list = self.hooks.get(name, [])
        hook_list.append(lambda *args, **kwargs: self._exception_free_callback(callback, *args, **kwargs))
        self.hooks[name] = hook_list

    def call_hook(self, name, **kwargs):
        """ Call all hooks registered with this name. Returns a list of the returns values of the hooks (in the order the hooks were added)"""
        return [y for y in [x(**kwargs) for x in self.hooks.get(name, [])] if y is not None]
