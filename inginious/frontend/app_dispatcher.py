# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from web import utils

# See Application Dispatching in Flask documentation
# https://flask.palletsprojects.com/en/1.1.x/patterns/appdispatch/?highlight=dispatching
class AppDispatcher(object):

    def __init__(self, webpy_wsgiapp, flask_app, get_mapping):
        self.webpy_app = webpy_wsgiapp
        self.flask_app = flask_app
        self.get_mapping = get_mapping

    def __call__(self, environ, start_response):
        urls = tuple(a for a, b in self.get_mapping())
        go_to_webpy = self._match(urls, environ.get("PATH_INFO", "").strip())
        app = self.webpy_app if go_to_webpy else self.flask_app
        return app(environ, start_response)

    def _match(self, mapping, value):
        for pat in mapping:
            if utils.re_compile(r"^%s\Z" % (pat,)).match(value):
                return True
        return False