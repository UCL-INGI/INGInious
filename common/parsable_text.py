""" Tools to parse text """
from docutils import core

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
        if self.mode == "HTML":
            return self.html(self.content)
        else:
            return self.rst(self.content)

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
        parts = core.publish_parts(source=string, writer_name='html')
        return parts['body_pre_docinfo'] + parts['fragment']
