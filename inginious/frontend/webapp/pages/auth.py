# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Auth page """
import web

from inginious.frontend.webapp.pages.utils import INGIniousPage


class AuthenticationPage(INGIniousPage):

    def process(self,auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise web.notfound()

        self.user_manager.set_session_redir_url(web.ctx.env.get('HTTP_REFERER', '/').rsplit("?logoff")[0])
        auth_link = auth_method.get_auth_link(self.user_manager)
        raise web.seeother(auth_link)

    def GET(self, auth_id):
        return self.process(auth_id)

    def POST(self, auth_id):
        return self.process(auth_id)


class CallbackPage(INGIniousPage):

    def process(self, auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise web.notfound()

        user = auth_method.callback(self.user_manager)
        if user:
            username, realname, email = user
            # TODO: Check if account linked, or create new account
            self.user_manager.connect_user(username, realname, email)

        raise web.seeother(self.user_manager.session_redir_url() if user else "/")

    def GET(self, auth_id):
        return self.process(auth_id)

    def POST(self, auth_id):
        return self.process(auth_id)