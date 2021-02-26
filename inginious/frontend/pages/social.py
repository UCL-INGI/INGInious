# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Auth page """
import flask
from flask import redirect
from werkzeug.exceptions import NotFound

from inginious.frontend.pages.utils import INGIniousPage, INGIniousAuthPage


class AuthenticationPage(INGIniousPage):
    def process_signin(self,auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise self.app.notfound(message=_("Auth method doesn't exist"))

        auth_storage = self.user_manager.session_auth_storage().setdefault(auth_id, {})
        auth_storage["redir_url"] = flask.request.referrer or '/'
        auth_storage["method"] = "signin"
        auth_link = auth_method.get_auth_link(auth_storage)
        return redirect(auth_link)

    def GET(self, auth_id):
        if self.user_manager.session_cookieless():
            return redirect("/auth/signin/" + auth_id)
        return self.process_signin(auth_id)

    def POST(self, auth_id):
        return self.process_signin(auth_id)


class CallbackPage(INGIniousPage):
    def process_callback(self, auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise self.app.notfound(message=_("Auth method doesn't exist."))

        auth_storage = self.user_manager.session_auth_storage().setdefault(auth_id, {})
        user = auth_method.callback(auth_storage)
        if user and auth_storage.get("method", "") == "signin":
            if not self.user_manager.bind_user(auth_id, user):
                return redirect("/signin?binderror")
        elif user and auth_storage.get("method", "") == "share":
            submission = self.submission_manager.get_submission(auth_storage["submissionid"], True)
            if submission:
                course = self.course_factory.get_course(submission["courseid"])
                task = course.get_task(submission["taskid"])
                auth_method.share(auth_storage, course, task, submission, self.user_manager.session_language())
            else:
                raise NotFound(description=_("Submission doesn't exist."))
        else:
            return redirect("/signin?callbackerror")

        return redirect(auth_storage.get("redir_url", "/"))

    def GET(self, auth_id):
        if self.user_manager.session_cookieless():
            return redirect("/auth/signin/" + auth_id)
        return self.process_callback(auth_id)

    def POST(self, auth_id):
        return self.process_callback(auth_id)


class SharePage(INGIniousAuthPage):
    def process_share(self, auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise NotFound(description=_("Auth method not found."))

        auth_storage = self.user_manager.session_auth_storage().setdefault(auth_id, {})
        auth_storage["redir_url"] = flask.request.referrer or '/'
        auth_storage["method"] = "share"
        auth_storage["submissionid"] = flask.request.args.get("submissionid", "") or flask.request.form.get("submissionid", "")
        auth_link = auth_method.get_auth_link(auth_storage, True)
        return redirect(auth_link)

    def GET(self, auth_id):
        if self.user_manager.session_cookieless():
            return redirect("/auth/share/" + auth_id)

        return self.process_share(auth_id)

    def POST(self, auth_id):
        return self.process_share(auth_id)
