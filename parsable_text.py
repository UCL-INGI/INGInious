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
""" Tools to parse text """
from docutils import core
import cgi

from common.base import INGIniousConfiguration


class ParsableText(object):

    """Allow to parse a string with different parsers"""

    def __init__(self, content, mode="rst"):
        """Init the object. Content is the string to be parsed. Mode is the parser to be used. Currently, only rst(reStructuredText) and HTML are supported"""
        if mode not in ["rst", "HTML"]:
            raise Exception("Unknown text parser: " + mode)
        if mode == "HTML" and ("allow_html" not in INGIniousConfiguration or INGIniousConfiguration["allow_html"] == False):
            raise Exception("HTML is not allowed")
        self.content = content
        self.mode = mode

    def parse(self):
        """Returns parsed text"""
        try:
            if self.mode == "HTML":
                return self.html(self.content)
            else:
                return self.rst(self.content)
        except:
            return "<b>Parsing failed</b>: <pre>"+cgi.escape(self.content)+"</pre>"

    def __str__(self):
        """Returns parsed text"""
        return self.parse()

    def __unicode__(self):
        """Returns parsed text"""
        return self.parse()

    def html(self, string):
        """Parses HTML"""
        if "allow_html" not in INGIniousConfiguration or INGIniousConfiguration["allow_html"] == False:
            raise Exception("HTML is not allowed")
        elif INGIniousConfiguration["allow_html"] == "tidy":
            import tidylib
            out, dummy = tidylib.tidy_fragment(string)
            return out
        else:
            return string

    def rst(self, string):
        """Parses reStructuredText"""
        overrides = {'initial_header_level': 3, 'doctitle_xform': False}
        parts = core.publish_parts(source=string, writer_name='html', settings_overrides=overrides)
        return parts['body_pre_docinfo'] + parts['fragment']
