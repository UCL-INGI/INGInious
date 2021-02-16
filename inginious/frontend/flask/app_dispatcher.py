# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from web import utils


# See Application Dispatching in Flask documentation
# https://flask.palletsprojects.com/en/1.1.x/patterns/appdispatch/?highlight=dispatching
class PathDispatcher(object):

    def __init__(self, webpy_app, flask_app):
        self.webpy_app = webpy_app
        self.flask_app = flask_app
        urls = (r"/flask",)
        self.urls = tuple((r"(/@[a-f0-9A-F_]*@)?" + a) for a in urls)

    def __call__(self, environ, start_response):
        go_to_flask = self._match(self.urls, environ.get("PATH_INFO", "").strip())
        app = self.flask_app if go_to_flask else self.webpy_app
        return app(environ, start_response)

    def _match(self, mapping, value):
        for pat in mapping:
            if utils.re_compile(r"^%s\Z" % (pat,)).match(value):
                return True
        return False