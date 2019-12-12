# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A set of tools to help to migrate to Jinja. There are devtools, that should never be used
    directly in the main branch.
"""

from lxml.html import fromstring, HTMLParser


def elements_equal(e1, e2):
    # you should probably put breakpoints everywhere on the "return False" lines.
    if e1.tag != e2.tag:
        return False
    if str(e1.text).strip() != str(e2.text).strip():
        return False
    if str(e1.tail).strip() != str(e2.tail).strip():
        return False
    if e1.attrib != e2.attrib:
        return False
    if len(e1) != len(e2):
        return False
    return all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))

def check_same_tpl(html_a, html_b):
    """ Given html_a and html_b, two HTML pages, check that they contain the same structure.
        Raises an exception if it's not the case. Otherwise, returns html_a.
    """
    structa = fromstring(str(html_a), parser=HTMLParser(remove_blank_text=True))
    structb = fromstring(str(html_b), parser=HTMLParser(remove_blank_text=True))
    if not elements_equal(structa, structb):
        raise Exception("The two templates do not contain the same thing!")
    return html_a