# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from werkzeug.routing import BaseConverter

from inginious.frontend.pages.utils_flask import INGIniousStaticPage
from inginious.frontend.pages.index import IndexPage
from inginious.frontend.pages.queue import QueuePage
from inginious.frontend.pages.courselist import CourseListPage
from inginious.frontend.pages.mycourses import MyCoursesPage
from inginious.frontend.pages.preferences.bindings import BindingsPage
from inginious.frontend.pages.preferences.delete import DeletePage
from inginious.frontend.pages.preferences.profile import ProfilePage
from inginious.frontend.pages.preferences.utils import PrefRedirectPage
from inginious.frontend.pages.utils_flask import SignInPage, LogOutPage
from inginious.frontend.pages.register import RegistrationPage
from inginious.frontend.pages.social import AuthenticationPage, CallbackPage, SharePage
from inginious.frontend.pages.course_register import CourseRegisterPage
from inginious.frontend.pages.course import CoursePage
from inginious.frontend.pages.tasks import TaskPage, TaskPageStaticDownload
from inginious.frontend.pages.lti import LTITaskPage, LTILaunchPage, LTIBindPage, LTIAssetPage, LTILoginPage
from inginious.frontend.pages.group import GroupPage
from inginious.frontend.pages.marketplace import MarketplacePage
from inginious.frontend.pages.marketplace_course import MarketplaceCoursePage

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
    flask_app.add_url_rule('/<cookieless:sessionid>signin', view_func=SignInPage.as_view('signinpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>logout', view_func=LogOutPage.as_view('logoutpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>register', view_func=RegistrationPage.as_view('registrationpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>queue', view_func=QueuePage.as_view('queuepage'))
    flask_app.add_url_rule('/<cookieless:sessionid>register/<courseid>', view_func=CourseRegisterPage.as_view('courseregisterpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>marketplace', view_func=MarketplacePage.as_view('marketplacepage'))
    flask_app.add_url_rule('/<cookieless:sessionid>marketplace/<courseid>', view_func=MarketplaceCoursePage.as_view('marketplacecoursepage'))
    flask_app.add_url_rule('/<cookieless:sessionid>course/<courseid>', view_func=CoursePage.as_view('coursepage'))
    flask_app.add_url_rule('/<cookieless:sessionid>course/<courseid>/<taskid>', view_func=TaskPage.as_view('taskpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>course/<courseid>/<taskid>/<path:path>', view_func=TaskPageStaticDownload.as_view('taskpagestaticdownload'))
    flask_app.add_url_rule('/<cookieless:sessionid>group/<courseid>', view_func=GroupPage.as_view('grouppage'))
    flask_app.add_url_rule('/<cookieless:sessionid>auth/signin/<auth_id>', view_func=AuthenticationPage.as_view('authenticationpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>auth/callback/<auth_id>', view_func=CallbackPage.as_view('callbackpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>auth/share/<auth_id>', view_func=SharePage.as_view('sharepage'))
    flask_app.add_url_rule('/<cookieless:sessionid>pages/<pageid>', view_func=INGIniousStaticPage.as_view('staticpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>courselist', view_func=CourseListPage.as_view('courselistpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>mycourses', view_func=MyCoursesPage.as_view('mycoursespage'))
    flask_app.add_url_rule('/<cookieless:sessionid>preferences', view_func=PrefRedirectPage.as_view('prefredirectpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>preferences/bindings', view_func=BindingsPage.as_view('bindingspage'))
    flask_app.add_url_rule('/<cookieless:sessionid>preferences/delete', view_func=DeletePage.as_view('deletepage'))
    flask_app.add_url_rule('/<cookieless:sessionid>preferences/profile', view_func=ProfilePage.as_view('profilepage'))
    flask_app.add_url_rule('/<cookieless:sessionid>lti/task', view_func=LTITaskPage.as_view('ltitaskpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>lti/<courseid>/<taskid>', view_func=LTILaunchPage.as_view('ltilaunchpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>lti/bind', view_func=LTIBindPage.as_view('ltibindpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>lti/login', view_func=LTILoginPage.as_view('ltiloginpage'))
    flask_app.add_url_rule('/<cookieless:sessionid>lti/asset/<path:asset_url>', view_func=LTIAssetPage.as_view('ltiassetpage'))

