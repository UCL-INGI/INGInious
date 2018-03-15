# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
from collections import namedtuple
import web

from http.cookies import SimpleCookie, CookieError

def fix_webpy_cookies():
    """
    Fixes a bug in web.py. See #208. PR is waiting to be merged upstream at https://github.com/webpy/webpy/pull/419
    TODO: remove me once PR is merged upstream.
    """

    try:
        web.webapi.parse_cookies('a="test"')  # make the bug occur
    except NameError:
        # monkeypatch web.py
        SimpleCookie.iteritems = SimpleCookie.items
        web.webapi.Cookie = namedtuple('Cookie', ['SimpleCookie', 'CookieError'])(SimpleCookie, CookieError)

    web.webapi.parse_cookies('a="test"')  # check if it's ok


if __name__ == '__main__':
    fix_webpy_cookies()