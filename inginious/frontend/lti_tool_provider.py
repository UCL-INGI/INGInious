# coding=utf-8
import web
from lti import ToolProvider


class LTIWebPyToolProvider(ToolProvider):
    '''
    ToolProvider that works with Web.py requests
    '''

    @classmethod
    def from_webpy_request(cls, secret=None):
        params = web.webapi.rawinput("POST")
        headers = web.ctx.env.copy()

        headers = dict([(k, headers[k])
                        for k in headers if
                        k.upper().startswith('HTTP_') or
                        k.upper().startswith('CONTENT_')])

        url = web.ctx.home + web.ctx.fullpath
        return cls.from_unpacked_request(secret, params, url, headers)
