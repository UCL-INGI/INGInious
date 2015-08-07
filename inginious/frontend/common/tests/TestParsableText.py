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
from inginious.frontend.common.parsable_text import ParsableText

class TestHookManager(object):
    def test_code(self):
        rendered = ParsableText.rst("""``test``""")
        assert "<code" in rendered and "</code>" in rendered

    def test_str(self):
        rendered = str(ParsableText.rst("""``test``"""))
        assert "<code" in rendered and "</code>" in rendered

    def test_unicode(self):
        rendered = unicode(ParsableText.rst(u"""``😁``"""))
        assert "<code" in rendered and "</code>" in rendered and u"😁" in rendered

    def test_html_tidy(self):
        rendered = ParsableText.html('<non existing tag></...>')
        assert '<non existing tag>' not in rendered

    def test_parsable_text_once(self):

        def fake_parser(input):
            fake_parser.count += 1
            return ""
        fake_parser.count = 0
        orig_rst = ParsableText.rst
        ParsableText.rst = fake_parser

        pt = ParsableText("""``test``""", "rst")
        pt.rst = fake_parser

        pt.parse()
        str(pt)
        unicode(pt)

        ParsableText.rst = orig_rst

        assert fake_parser.count == 1

    def test_wrong_rst_injection(self):
        rendered = unicode(ParsableText.rst(
            """
            makefail_
            <script type="text/javascript">alert('Eh, XSS injection!');</script>
            """
        ))
        assert "&lt;script type=&quot;text/javascript&quot;&gt;" in rendered

    def test_failing_parser_injection(self):
        def fake_parser(input):
            raise Exception()

        fake_parser.count = 0
        orig_rst = ParsableText.rst
        ParsableText.rst = fake_parser

        pt = ParsableText("""<script type="text/javascript">alert('Eh, XSS injection!');</script>""")
        rendered = pt.parse()

        ParsableText.rst = orig_rst

        assert "&lt;script " in rendered
