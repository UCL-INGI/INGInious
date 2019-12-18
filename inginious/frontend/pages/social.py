# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Auth page """
import web
from pymongo import ReturnDocument

from inginious.frontend.pages.utils import INGIniousAuthPage
from inginious.frontend.pages.utils import INGIniousPage


class AuthenticationPage(INGIniousPage):
    def process_signin(self,auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise web.notfound()

        auth_storage = self.user_manager.session_auth_storage().setdefault(auth_id, {})
        auth_storage["redir_url"] = web.ctx.env.get('HTTP_REFERER', '/')
        auth_storage["method"] = "signin"
        auth_link = auth_method.get_auth_link(auth_storage)
        raise web.seeother(auth_link)

    def GET(self, auth_id):
        if self.user_manager.session_cookieless():
            raise web.seeother("/auth/signin/" + auth_id)
        return self.process_signin(auth_id)

    def POST(self, auth_id):
        return self.process_signin(auth_id)


class CallbackPage(INGIniousPage):
    def process_callback(self, auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise web.notfound()

        auth_storage = self.user_manager.session_auth_storage().setdefault(auth_id, {})
        user = auth_method.callback(auth_storage)
        if user and auth_storage.get("method", "") == "signin":
            if not self.user_manager.bind_user(auth_id, user):
                raise web.seeother("/signin?binderror")
        elif user and auth_storage.get("method", "") == "share":
            submission = self.submission_manager.get_submission(auth_storage["submissionid"], True)
            if submission:
                course = self.course_factory.get_course(submission["courseid"])
                task = course.get_task(submission["taskid"])
                auth_method.share(auth_storage, course, task, submission, self.user_manager.session_language())
            else:
                raise web.notfound()
        else:
            raise web.seeother("/signin?callbackerror")

        raise web.seeother(auth_storage.get("redir_url", "/"))

    def GET(self, auth_id):
        if self.user_manager.session_cookieless():
            raise web.seeother("/auth/signin/" + auth_id)
        return self.process_callback(auth_id)

    def POST(self, auth_id):
        return self.process_callback(auth_id)


class SharePage(INGIniousAuthPage):
    def process_share(self, auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise web.notfound()

        auth_storage = self.user_manager.session_auth_storage().setdefault(auth_id, {})
        auth_storage["redir_url"] = web.ctx.env.get('HTTP_REFERER', '/')
        auth_storage["method"] = "share"
        auth_storage["submissionid"] = web.input().get("submissionid", "")
        auth_link = auth_method.get_auth_link(auth_storage, True)
        raise web.seeother(auth_link)

    def GET(self, auth_id):
        if self.user_manager.session_cookieless():
            raise web.seeother("/auth/share/" + auth_id)

        return self.process_share(auth_id)

    def POST(self, auth_id):
        return self.process_share(auth_id)
