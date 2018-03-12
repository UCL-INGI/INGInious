# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Hook Manager """
import logging
import bisect


class HookManager(object):
    """ Registers an manages hooks. Hooks are callback functions called when the inginious.backend does a specific action. """

    def __init__(self):
        self._hooks = {}
        self._logger = logging.getLogger("inginious.common.hookmanager")

    def _exception_free_callback(self, callback, *args, **kwargs):
        """ A wrapper that remove all exceptions raised from hooks """
        try:
            return callback(*args, **kwargs)
        except Exception:
            self._logger.exception("An exception occurred while calling a hook! ",exc_info=True)
            return None

    def add_hook(self, name, callback, prio=0):
        """ Add a new hook that can be called with the call_hook function.
            `prio` is the priority. Higher priority hooks are called before lower priority ones.
            This function does not enforce a particular order between hooks with the same priorities.
        """
        hook_list = self._hooks.get(name, [])

        add = (lambda *args, **kwargs: self._exception_free_callback(callback, *args, **kwargs)), -prio
        pos = bisect.bisect_right(list(x[1] for x in hook_list), -prio)
        hook_list[pos:pos] = [add]

        self._hooks[name] = hook_list

    def call_hook(self, name, **kwargs):
        """ Call all hooks registered with this name. Returns a list of the returns values of the hooks (in the order the hooks were added)"""
        return [y for y in [x(**kwargs) for x, _ in self._hooks.get(name, [])] if y is not None]

    def call_hook_recursive(self, name, **kwargs):
        """ Call all hooks registered with this name. Each hook receives as arguments the return value of the
            previous hook call, or the initial params for the first hook. As such, each hook must return a dictionary
            with the received (eventually modified) args. Returns the modified args."""
        for x, _ in self._hooks.get(name, []):
            out = x(**kwargs)
            if out is not None: #ignore already reported failure
                kwargs = out
        return kwargs