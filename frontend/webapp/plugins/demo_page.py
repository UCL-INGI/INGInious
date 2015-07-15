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
""" A demo plugin that adds a page """


class DemoPage(object):
    """ A simple demo page showing how to add a new page """

    def GET(self):
        """ GET request """
        return "This is a test page :-)"


def init(plugin_manager, _, _2, _3):
    """ Init the plugin """
    plugin_manager.add_page("/test", "webapp.plugins.demo_page.DemoPage")
    print "Started Demo Page"
