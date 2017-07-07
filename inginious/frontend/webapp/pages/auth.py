# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Auth page """
import web

from pymongo import ReturnDocument
from inginious.frontend.webapp.pages.utils import INGIniousPage


class AuthenticationPage(INGIniousPage):

    def process_signin(self,auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise web.notfound()

        self.user_manager.set_session_redir_url(web.ctx.env.get('HTTP_REFERER', '/').rsplit("?logoff")[0])
        auth_link = auth_method.get_auth_link(self.user_manager)
        raise web.seeother(auth_link)

    def process_callback(self, auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise web.notfound()

        user = auth_method.callback(self.user_manager)
        if user:
            username, realname, email = user

            # Look for already bound auth method username
            user_profile = self.database.users.find_one({"bindings." + auth_id: username})

            if user_profile and not self.user_manager.session_logged_in():
                # Sign in
                self.user_manager.connect_user(user_profile["username"], user_profile["realname"], user_profile["email"])
            elif user_profile and self.user_manager.session_username() == user_profile["username"]:
                # Logged in, refresh fields if found profile username matches session username
                pass
            elif user_profile:
                # Logged in, but already linked to another account
                pass
            elif self.user_manager.session_logged_in():
                # No binding, but logged: add new binding
                self.database.users.find_one_and_update({"username": self.user_manager.session_username()},
                                                        {"$set": {"bindings." + auth_id: [username, {}]}},
                                                        return_document=ReturnDocument.AFTER)

            else:
                # No binding, check for email
                user_profile = self.database.users.find_one({"email": email})
                if user_profile:
                    # Found an email, existing user account, abort without binding
                    pass
                else:
                    # New user, create an account using email address
                    self.database.users.insert({"username": username,
                                                "realname": realname,
                                                "email": email,
                                                "bindings": {auth_id: [username, {}]}})
                    self.user_manager.connect_user(username, realname, email)

        raise web.seeother(self.user_manager.session_redir_url())

    def GET(self, auth_id, method):
        if method == "signin":
            return self.process_signin(auth_id)
        else:
            return self.process_callback(auth_id)

    def POST(self, auth_id, method):
        if method == "signin":
            return self.process_signin(auth_id)
        else:
            return self.process_callback(auth_id)