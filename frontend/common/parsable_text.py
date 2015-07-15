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
""" Tools to parse text """
import cgi

from docutils import core, nodes
from docutils.writers import html4css1
import tidylib


class _CustomHTMLWriter(html4css1.Writer, object):
    """ A custom HTML writer that fixes some defaults of docutils... """

    def __init__(self):
        html4css1.Writer.__init__(self)
        self.translator_class = self._CustomHTMLTranslator

    class _CustomHTMLTranslator(html4css1.HTMLTranslator, object):
        """ A custom HTML translator """

        def visit_literal(self, node):
            """ A custom version of visit_literal that uses the balise <code> instead of <tt>. """
            # special case: "code" role
            classes = node.get('classes', [])
            if 'code' in classes:
                # filter 'code' from class arguments
                node['classes'] = [cls for cls in classes if cls != 'code']
                self.body.append(self.starttag(node, 'code', ''))
                return
            self.body.append(
                self.starttag(node, 'code', '', CLASS='docutils literal'))
            text = node.astext()
            for token in self.words_and_spaces.findall(text):
                if token.strip():
                    # Protect text like "--an-option" and the regular expression
                    # ``[+]?(\d+(\.\d*)?|\.\d+)`` from bad line wrapping
                    if self.sollbruchstelle.search(token):
                        self.body.append('<span class="pre">%s</span>'
                                         % self.encode(token))
                    else:
                        self.body.append(self.encode(token))
                elif token in ('\n', ' '):
                    # Allow breaks at whitespace:
                    self.body.append(token)
                else:
                    # Protect runs of multiple spaces; the last space can wrap:
                    self.body.append('&nbsp;' * (len(token) - 1) + ' ')
            self.body.append('</code>')
            # Content already processed:
            raise nodes.SkipNode


class ParsableText(object):
    """Allow to parse a string with different parsers"""

    def __init__(self, content, mode="rst"):
        """Init the object. Content is the string to be parsed. Mode is the parser to be used. Currently, only rst(reStructuredText) and HTML are supported"""
        if mode not in ["rst", "HTML"]:
            raise Exception("Unknown text parser: " + mode)
        self._content = content
        self._parsed = None
        self._mode = mode

    def original_content(self):
        """ Returns the original content """
        return self._content

    def parse(self):
        """Returns parsed text"""
        if self._parsed is None:
            try:
                if self._mode == "HTML":
                    self._parsed = self.html(self._content)
                else:
                    self._parsed = self.rst(self._content)
            except:
                self._parsed = "<b>Parsing failed</b>: <pre>" + cgi.escape(self._content) + "</pre>"
        return self._parsed

    def __str__(self):
        """Returns parsed text"""
        return self.parse()

    def __unicode__(self):
        """Returns parsed text"""
        return self.parse()

    def html(self, string):
        """Parses HTML"""
        out, _ = tidylib.tidy_fragment(string)
        return out

    def rst(self, string):
        """Parses reStructuredText"""
        overrides = {'initial_header_level': 3, 'doctitle_xform': False}
        parts = core.publish_parts(source=string, writer=_CustomHTMLWriter(), settings_overrides=overrides)
        return parts['body_pre_docinfo'] + parts['fragment']
