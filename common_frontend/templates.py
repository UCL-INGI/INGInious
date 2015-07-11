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
""" Basic dependencies for the webapp """
import os

import web

from common.singleton import Singleton
from common_frontend.plugin_manager import PluginManager


def add_to_template_globals(name, value):
    """ Add a variable to will be accessible in the templates """
    add_to_template_globals.globals[name] = value

add_to_template_globals.globals = {}

def get_custom_template_renderer(dir_path, base=None):
    """ Create a template renderer on templates in the directory specified.
        *base* is the base layout name.
    """
    base_dir_path = os.path.join(os.path.dirname(__file__), '..') # INGInious root
    return web.template.render(os.path.join(base_dir_path, dir_path), globals=add_to_template_globals.globals, base=base)

class TemplateHelper(object):
    """ Class accessible from templates that calls function defined in the Python part of the code. Singleton class. """

    __metaclass__ = Singleton
    _base_helpers = {}  # see __init__
    WEB_CTX_KEY = "inginious_tpl_helper"

    def __init__(self):
        self._base_helpers = {"header_hook": (lambda **kwargs: self._generic_hook('header_html', **kwargs)),
                              "course_menu": (lambda **kwargs: self._generic_hook('course_menu', **kwargs)),
                              "javascript_header": (lambda **_: self._javascript_helper("header")),
                              "javascript_footer": (lambda **_: self._javascript_helper("footer")),
                              "css": (lambda **_: self._css_helper())}

    def call(self, name, **kwargs):
        helpers = dict(self._base_helpers.items() + PluginManager().call_hook("template_helper"))
        if helpers.get(name, None) is None:
            return ""
        else:
            return helpers[name](**kwargs)

    def add_javascript(self, link, position="footer"):
        """ Add a javascript file to load. Position can either be "header" or "footer" """
        self._get_ctx()["javascript"][position].append(link)

    def add_css(self, link):
        """ Add a css file to load """
        self._get_ctx()["css"].append(link)

    def add_other(self, name, func):
        """ Add another callback to the template helper """
        self._base_helpers[name] = func

    def _javascript_helper(self, position):
        """ Add javascript links for the current page and for the plugins """
        if position not in ["header", "footer"]:
            position = "footer"

        # Load javascript files from plugins
        if position == "header":
            entries = [entry for entry in PluginManager().call_hook("javascript_header") if entry is not None]
        else:
            entries = [entry for entry in PluginManager().call_hook("javascript_footer") if entry is not None]
        # Load javascript for the current page
        entries += self._get_ctx()["javascript"][position]
        entries = ["<script src='" + entry + "' type='text/javascript' charset='utf-8'></script>" for entry in entries]
        return "\n".join(entries)

    def _css_helper(self):
        """ Add CSS links for the current page and for the plugins """
        entries = [entry for entry in PluginManager().call_hook("css") if entry is not None]
        # Load javascript for the current page
        entries += self._get_ctx()["css"]
        entries = ["<link href='" + entry + "' rel='stylesheet'>" for entry in entries]
        return "\n".join(entries)

    def _get_ctx(self):
        """ Get web.ctx object for the Template helper """
        if self.WEB_CTX_KEY not in web.ctx:
            web.ctx[self.WEB_CTX_KEY] = {
                "javascript": {"footer": [], "header": []},
                "css": []}
        return web.ctx.get(self.WEB_CTX_KEY)

    def _generic_hook(self, name, **kwargs):
        """ A generic hook that links the TemplateHelper with PluginManager """
        entries = [entry for entry in PluginManager().call_hook(name, **kwargs) if entry is not None]
        return "\n".join(entries)

def get_renderer(with_layout=True):
    """ Get the default renderer, initialized by init_renderer."""
    if not get_renderer.renderer:
        raise Exception("init_renderer should be called before using get_renderer")
    if with_layout:
        return get_renderer.renderer
    else:
        return get_renderer.renderer_nolayout

get_renderer.renderer = None
get_renderer.renderer_nolayout = None

def init_renderer(template_dir, layout):
    """ Initialize all the renderers """
    get_renderer.renderer = get_custom_template_renderer(template_dir, layout)
    get_renderer.renderer_nolayout = get_custom_template_renderer(template_dir)

    add_to_template_globals.globals["include"] = get_custom_template_renderer(template_dir)
    add_to_template_globals.globals["template_helper"] = TemplateHelper()
