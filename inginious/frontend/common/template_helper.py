# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" TemplateManager """
import os

import web


class TemplateHelper(object):
    """ Class accessible from templates that calls function defined in the Python part of the code. """

    _base_helpers = {}  # see __init__
    WEB_CTX_KEY = "inginious_tpl_helper"

    """ The absolute path to inginious package"""
    INGINIOUS_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    def __init__(self, plugin_manager, default_template_dir, default_layout, use_minified=True):
        self._base_helpers = {"header_hook": (lambda **kwargs: self._generic_hook('header_html', **kwargs)),
                              "course_menu": (lambda **kwargs: self._generic_hook('course_menu', **kwargs)),
                              "task_menu": (lambda **kwargs: self._generic_hook('task_menu', **kwargs)),
                              "javascript_header": (lambda **_: self._javascript_helper("header")),
                              "javascript_footer": (lambda **_: self._javascript_helper("footer")),
                              "css": (lambda **_: self._css_helper())}
        self._plugin_manager = plugin_manager
        self._template_dir = default_template_dir
        self._layout = default_layout

        self._template_globals = {}

        self._default_renderer = self.get_custom_template_renderer(default_template_dir, default_layout)
        self._default_renderer_nolayout = self.get_custom_template_renderer(default_template_dir)
        self._default_common_renderer = self.get_custom_template_renderer(os.path.join(os.path.dirname(__file__), "templates"))

        self.add_to_template_globals("include", self._default_renderer_nolayout)
        self.add_to_template_globals("template_helper", self)
        self.add_to_template_globals("plugin_manager", plugin_manager)
        self.add_to_template_globals("use_minified", use_minified)

    def get_renderer(self, with_layout=True):
        """ Get the default renderer """
        return self._default_renderer if with_layout else self._default_renderer_nolayout

    def get_common_renderer(self):
        """ Get the default renderer for templates in the inginious.frontend.common package"""
        return self._default_common_renderer

    def add_to_template_globals(self, name, value):
        """ Add a variable to will be accessible in the templates """
        self._template_globals[name] = value

    def get_custom_template_renderer(self, dir_path, base=None):
        """ Create a template renderer on templates in the directory specified.
            *base* is the base layout name.
        """
        return web.template.render(os.path.join(self.INGINIOUS_ROOT_PATH, dir_path), globals=self._template_globals, base=base)

    def call(self, name, **kwargs):
        helpers = dict(list(self._base_helpers.items()) + self._plugin_manager.call_hook("template_helper"))
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
            entries = [entry for entry in self._plugin_manager.call_hook("javascript_header") if entry is not None]
        else:
            entries = [entry for entry in self._plugin_manager.call_hook("javascript_footer") if entry is not None]
        # Load javascript for the current page
        entries += self._get_ctx()["javascript"][position]
        entries = ["<script src='" + entry + "' type='text/javascript' charset='utf-8'></script>" for entry in entries]
        return "\n".join(entries)

    def _css_helper(self):
        """ Add CSS links for the current page and for the plugins """
        entries = [entry for entry in self._plugin_manager.call_hook("css") if entry is not None]
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
        entries = [entry for entry in self._plugin_manager.call_hook(name, **kwargs) if entry is not None]
        return "\n".join(entries)
