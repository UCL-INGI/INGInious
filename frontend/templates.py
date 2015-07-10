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
""" Basic dependencies for the frontend """
import os
import web
import frontend.pages
from frontend.plugins.plugin_manager import PluginManager

def add_to_template_globals(name, value):
    """ Add a variable to will be accessible in the templates """
    add_to_template_globals.globals[name] = value

add_to_template_globals.globals = {}

def get_template_renderer(dir_path, base=None):
    """ Create a template renderer on templates in the directory specified.
        *base* is the base layout name.
    """
    base_dir_path = os.path.dirname(__file__)
    return web.template.render(os.path.join(base_dir_path, dir_path), globals=add_to_template_globals.globals, base=base)

renderer = get_template_renderer('templates/', 'layout')
add_to_template_globals.globals["include"] = get_template_renderer('templates/')

def generic_hook(name, **kwargs):
    """ A generic hook that links the TemplateHelper with PluginManager """
    entries = [entry for entry in PluginManager.get_instance().call_hook(name, **kwargs) if entry is not None]
    return "\n".join(entries)

class TemplateHelper(object):
    """ Class accessible from templates that calls function defined in the Python part of the code """

    _instance = None
    _base_helpers = {}  # see __init__
    WEB_CTX_KEY = "inginious_tpl_helper"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TemplateHelper, cls).__new__(
                cls, *args, **kwargs)
            add_to_template_globals("template_helper", cls._instance)
        else:
            raise Exception("You should not instanciate PluginManager more than once")
        return cls._instance

    def __init__(self):
        self._base_helpers = {"header_hook": (lambda **kwargs: generic_hook('header_html', **kwargs)),
                              "course_menu": (lambda **kwargs: generic_hook('course_menu', **kwargs)),
                              "javascript_header": (lambda **_: TemplateHelper._javascript_helper("header")),
                              "javascript_footer": (lambda **_: TemplateHelper._javascript_helper("footer")),
                              "css": (lambda **_: TemplateHelper._css_helper()),
                              "course_admin_menu": frontend.pages.course_admin.utils.get_menu}

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

    def add_javascript(self, link, position="footer"):
        """ Add a javascript file to load. Position can either be "header" or "footer" """
        self._get_ctx()["javascript"][position].append(link)

    def add_css(self, link):
        """ Add a css file to load """
        self._get_ctx()["css"].append(link)

    @classmethod
    def _javascript_helper(cls, position):
        """ Add javascript links for the current page and for the plugins """
        if position not in ["header", "footer"]:
            position = "footer"

        # Load javascript files from plugins
        if position == "header":
            entries = [entry for entry in PluginManager.get_instance().call_hook("javascript_header") if entry is not None]
        else:
            entries = [entry for entry in PluginManager.get_instance().call_hook("javascript_footer") if entry is not None]
        # Load javascript for the current page
        entries += cls.get_instance()._get_ctx()["javascript"][position]
        entries = ["<script src='" + entry + "' type='text/javascript' charset='utf-8'></script>" for entry in entries]
        return "\n".join(entries)

    @classmethod
    def _css_helper(cls):
        """ Add CSS links for the current page and for the plugins """
        entries = [entry for entry in PluginManager.get_instance().call_hook("css") if entry is not None]
        # Load javascript for the current page
        entries += cls.get_instance()._get_ctx()["css"]
        entries = ["<link href='" + entry + "' rel='stylesheet'>" for entry in entries]
        return "\n".join(entries)

    def _get_ctx(self):
        """ Get web.ctx object for the Template helper """
        if self.WEB_CTX_KEY not in web.ctx:
            web.ctx[self.WEB_CTX_KEY] = {
                "javascript": {"footer": [], "header": []},
                "css": []}
        return web.ctx.get(self.WEB_CTX_KEY)