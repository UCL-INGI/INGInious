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
""" Hook Manager """


class HookManager(object):
    """ Registers an manages hooks. Hooks are callback functions called when the inginious.backend does a specific action. """

    def __init__(self):
        self.hooks = {}

    def _exception_free_callback(self, callback, *args, **kwargs):
        """ A wrapper that remove all exceptions raised from hooks """
        try:
            return callback(*args, **kwargs)
        except Exception as e:
            print "An exception occured while calling a hook! " + str(e)
            return None

    def add_hook(self, name, callback):
        """ Add a new hook that can be called with the call_hook function """
        hook_list = self.hooks.get(name, [])
        hook_list.append(lambda *args, **kwargs: self._exception_free_callback(callback, *args, **kwargs))
        self.hooks[name] = hook_list

    def call_hook(self, name, **kwargs):
        """ Call all hooks registered with this name. Returns a list of the returns values of the hooks (in the order the hooks were added)"""
        return [y for y in [x(**kwargs) for x in self.hooks.get(name, [])] if y is not None]
