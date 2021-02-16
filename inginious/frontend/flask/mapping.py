# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from werkzeug.routing import BaseConverter

from inginious.frontend.pages.utils_flask import INGIniousStaticPage
from inginious.frontend.pages.index import IndexPage


class CookielessConverter(BaseConverter):
    # Parse the cookieless sessionid at the beginning of the url
    regex = r"((@)([a-f0-9A-F_]*)(@/))?"

    def to_python(self, value):
        return value[1:-2]

    def to_url(self, value):
        return "@" + str(value) + "@/"


def init_flask_mapping(flask_app):
    flask_app.url_map.converters['cookieless'] = CookielessConverter
    flask_app.add_url_rule('/<cookieless:sessionid>', view_func=IndexPage.as_view('indexpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>index', view_func=IndexPage.as_view('indexpage.alias'))
    flask_app.add_url_rule('/<cookieless:sessionid>pages/<pageid>', view_func=INGIniousStaticPage.as_view('staticpage'))