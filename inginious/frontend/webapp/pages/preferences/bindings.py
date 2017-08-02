# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Auth bindings page """
import web

from pymongo import ReturnDocument
from inginious.frontend.webapp.pages.utils import INGIniousAuthPage


class BindingsPage(INGIniousAuthPage):
    """ Bindings page for DB-authenticated users"""

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """ GET request """
        auth_methods = self.user_manager.get_auth_methods()
        user_data = self.database.users.find_one({"username": self.user_manager.session_username()})
        bindings = user_data.get("bindings", {})
        return self.template_helper.get_renderer().preferences.bindings(bindings, auth_methods, "", False)

    def POST_AUTH(self):  # pylint: disable=arguments-differ
        """ POST request """
        msg = ""
        error = False

        user_data = self.database.users.find_one({"username": self.user_manager.session_username()})

        if not user_data:
            raise web.notfound()

        user_input = web.input()
        auth_methods = self.user_manager.get_auth_methods()

        if "auth_binding" in user_input:
            auth_binding = user_input["auth_binding"]

            if auth_binding not in auth_methods.keys():
                error = True
                msg = "Incorrect authentication binding."
            elif auth_binding not in user_data.get("bindings", {}):
                raise web.seeother("/auth/" + auth_binding +"/signin")
        elif "revoke_auth_binding" in user_input:
            auth_id = user_input["revoke_auth_binding"]

            if auth_id not in auth_methods.keys():
                error = True
                msg = "Incorrect authentication binding."
            elif len(user_data.get("bindings", {}).keys()) > 1 or "password" in user_data:
                user_data = self.database.users.find_one_and_update({"username": self.user_manager.session_username()},
                                                        {"$unset": {"bindings." + auth_id: 1}})
            else:
                error = True
                msg = "You must set a password before removing all bindings."

        bindings = user_data.get("bindings", {})

        return self.template_helper.get_renderer().preferences.bindings(bindings, auth_methods, msg, error)