# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from flask import request
from lti import ToolProvider


class LTIWebPyToolProvider(ToolProvider):
    '''
    ToolProvider that works with Web.py requests
    '''

    @classmethod
    def from_webpy_request(cls, secret=None):
        params = request.form.copy()
        headers = request.headers.environ.copy()

        headers = dict([(k, headers[k])
                        for k in headers if
                        k.upper().startswith('HTTP_') or
                        k.upper().startswith('CONTENT_')])

        url = request.url
        return cls.from_unpacked_request(secret, params, url, headers)
