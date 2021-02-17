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
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.parsable_text import ParsableText
from werkzeug.exceptions import NotFound

class INGIniousFlaskPage(INGIniousPage, MethodView):
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


class INGIniousStaticPage(INGIniousFlaskPage):
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