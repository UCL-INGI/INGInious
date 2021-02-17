# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some utils for all the pages """
import os
import flask
from flask import session, redirect, url_for, request
from flask.views import MethodView

from inginious.common import custom_yaml
from inginious.frontend.pages.utils import INGIniousPage as INGIniousWebPyPage
from inginious.frontend.parsable_text import ParsableText
from werkzeug.exceptions import NotFound, NotAcceptable

class INGIniousPage(INGIniousWebPyPage, MethodView):
    @property
    def app(self):
        """ Returns the web application singleton """
        return flask.current_app

    def _pre_check(self, sessionid):
        # Check for cookieless redirect
        if not sessionid and session.get("cookieless", False):
            query_string = "?" + request.query_string.decode("utf-8") if request.query_string else ""
            request.view_args.update(sessionid=session.get("session_id"))
            return redirect(url_for(request.endpoint, **request.view_args) + query_string)

        # Check for language
        if "lang" in request.args and request.args["lang"] in self.app.l10n_manager.translations.keys():
            self.user_manager.set_session_language(request.args["lang"])
        elif "language" not in session:
            best_lang = request.accept_languages.best_match(self.app.l10n_manager.translations.keys(), default="en")
            self.user_manager.set_session_language(best_lang)

        return ""

    def get(self, sessionid, *args, **kwargs):
        pre_check = self._pre_check(sessionid)
        return pre_check if pre_check else self.GET(*args, **kwargs)

    def post(self, sessionid, *args, **kwargs):
        pre_check = self._pre_check(sessionid)
        return pre_check if pre_check else self.POST(*args, **kwargs)


class INGIniousAuthPage(INGIniousPage):
    """
    Augmented version of INGIniousPage that checks if user is authenticated.
    """

    def POST_AUTH(self, *args, **kwargs):  # pylint: disable=unused-argument
        raise NotAcceptable()

    def GET_AUTH(self, *args, **kwargs):  # pylint: disable=unused-argument
        raise NotAcceptable()

    def GET(self, *args, **kwargs):
        """
        Checks if user is authenticated and calls GET_AUTH or performs logout.
        Otherwise, returns the login template.
        """
        if self.user_manager.session_logged_in():
            if (not self.user_manager.session_username() or (self.app.terms_page is not None and
                                                             self.app.privacy_page is not None and
                                                             not self.user_manager.session_tos_signed()))\
                    and not self.__class__.__name__ == "ProfilePage":
                return redirect("/preferences/profile")

            if not self.is_lti_page and self.user_manager.session_lti_info() is not None: #lti session
                self.user_manager.disconnect_user()
                return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods())

            return self.GET_AUTH(*args, **kwargs)
        elif self.preview_allowed(*args, **kwargs):
            return self.GET_AUTH(*args, **kwargs)
        else:
            error = ''
            if "binderror" in request.args:
                error = _("An account using this email already exists and is not bound with this service. "
                          "For security reasons, please log in via another method and bind your account in your profile.")
            if "callbackerror" in request.args:
                error = _("Couldn't fetch the required information from the service. Please check the provided "
                          "permissions (name, email) and contact your INGInious administrator if the error persists.")
            return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods(), error=error)

    def POST(self, *args, **kwargs):
        """
        Checks if user is authenticated and calls POST_AUTH or performs login and calls GET_AUTH.
        Otherwise, returns the login template.
        """
        if self.user_manager.session_logged_in():
            if not self.user_manager.session_username() and not self.__class__.__name__ == "ProfilePage":
                return redirect("/preferences/profile")

            if not self.is_lti_page and self.user_manager.session_lti_info() is not None:  # lti session
                self.user_manager.disconnect_user()
                return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods())

            return self.POST_AUTH(*args, **kwargs)
        else:
            user_input = request.form
            if "login" in user_input and "password" in user_input:
                if self.user_manager.auth_user(user_input["login"].strip(), user_input["password"]) is not None:
                    return self.GET_AUTH(*args, **kwargs)
                else:
                    return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods(), error=_("Invalid login/password"))
            elif self.preview_allowed(*args, **kwargs):
                return self.POST_AUTH(*args, **kwargs)
            else:
                return self.template_helper.render("auth.html", auth_methods=self.user_manager.get_auth_methods())

    def preview_allowed(self, *args, **kwargs):
        """
            If this function returns True, the auth check is disabled.
            Override this function with a custom check if needed.
        """
        return False


class INGIniousStaticPage(INGIniousPage):
    cache = {}

    def GET(self, pageid):
        return self.show_page(pageid)

    def POST(self, pageid):
        return self.show_page(pageid)

    def show_page(self, page):
        static_directory = self.app.static_directory
        language = self.user_manager.session_language()

        # Check for the file
        filename = None
        mtime = None
        filepaths = [os.path.join(static_directory, page + ".yaml"),
                     os.path.join(static_directory, page + "." + language + ".yaml")]

        for filepath in filepaths:
            if os.path.exists(filepath):
                filename = filepath
                mtime = os.stat(filepath).st_mtime

        if not filename:
            raise NotFound(description=_("File doesn't exist."))

        # Check and update cache
        if INGIniousStaticPage.cache.get(filename, (0, None))[0] < mtime:
            with open(filename, "r") as f:
                INGIniousStaticPage.cache[filename] = mtime, custom_yaml.load(f)

        filecontent = INGIniousStaticPage.cache[filename][1]
        title = filecontent["title"]
        content = ParsableText.rst(filecontent["content"], initial_header_level=2)

        return self.template_helper.render("static.html", pagetitle=title, content=content)