# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from werkzeug.routing import BaseConverter

from inginious.frontend.pages.utils_flask import INGIniousStaticPage
from inginious.frontend.pages.index import IndexPage
from inginious.frontend.pages.courselist import CourseListPage
from inginious.frontend.pages.preferences.bindings import BindingsPage
from inginious.frontend.pages.preferences.delete import DeletePage
from inginious.frontend.pages.preferences.profile import ProfilePage
from inginious.frontend.pages.preferences.utils import PrefRedirectPage

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
    flask_app.add_url_rule('/<cookieless:sessionid>courselist', view_func=CourseListPage.as_view('courselistpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>preferences', view_func=PrefRedirectPage.as_view('prefredirectpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>preferences/bindings', view_func=BindingsPage.as_view('bindingspage'))
    flask_app.add_url_rule('/<cookieless:sessionid>preferences/delete', view_func=DeletePage.as_view('deletepage'))
    flask_app.add_url_rule('/<cookieless:sessionid>preferences/profile', view_func=ProfilePage.as_view('profilepage'))

