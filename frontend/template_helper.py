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
""" Helper for the templates """

from frontend.base import add_to_template_globals
import frontend.pages.course_admin.utils
from frontend.plugins.plugin_manager import PluginManager


def generic_hook(name, **kwargs):
    """ A generic hook that links the TemplateHelper with PluginManager """
    entries = [entry for entry in PluginManager.get_instance().call_hook(name, **kwargs) if entry is not None]
    return "\n".join(entries)


class TemplateHelper(object):

    """ Class accessible from templates that calls function defined in the Python part of the code """

    _instance = None
    _base_helpers = {"header_hook": (lambda **kwargs: generic_hook('header_html', **kwargs)),
                     "course_menu": (lambda **kwargs: generic_hook('course_menu', **kwargs)),
                     "course_admin_menu": frontend.pages.course_admin.utils.get_menu}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TemplateHelper, cls).__new__(
                cls, *args, **kwargs)
            add_to_template_globals("template_helper", cls._instance)
        else:
            raise Exception("You should not instanciate PluginManager more than once")
        return cls._instance

    @classmethod
    def get_instance(cls):
        """ get the instance of TemplateHelper """
        return cls._instance

    def call(self, name, **kwargs):
        helpers = dict(self._base_helpers.items() + PluginManager.get_instance().call_hook("template_helper"))
        if helpers.get(name, None) is None:
            return ""
        else:
            return helpers.get(name, None)(**kwargs)
