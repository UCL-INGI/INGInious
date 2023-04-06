# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Admin index page"""
import json

from flask import request, jsonify

from inginious.frontend.pages.utils import INGIniousAdministratorPage


class AdministrationUsersPage(INGIniousAdministratorPage):
    """User Admin page."""

    def GET_AUTH(self, *args, **kwargs):
        """ Display admin users page """
        return self.show_page()

    def POST_AUTH(self, *args, **kwargs):
        """ Display admin users page"""
        return self.show_page()

    def show_page(self):
        """Display page"""
        user_input = request.form
        if "displayed_selection" in user_input:
            # Mostly happened when changing page
            params = json.loads(user_input.get("displayed_selection", ""))
        else:
            params={"limit":10,"sort_by":"username","order":1}
            for key in ["username", "realname", "email"]:
                params[key] = user_input[key] if key in user_input else ""
            if "activated" in user_input:
                params["activated"] = user_input["activated"]
            if "sort_by" in user_input and "order" in user_input:
                params["sort_by"]=user_input["sort_by"]
                params["order"]= int(user_input["order"])
            if "limit" in user_input:
                params["limit"] = int(user_input["limit"])
        query = {}
        for key in ["username","realname","email"]:
            query[key]={'$regex': f".*{params[key]}.*"}
        if 'activated' in params:
            query["activate"] = {'$exists': not params["activated"]}
        usernames = [x['username'] for x in
                     self.database.users.find(query)]
        page = int(user_input.get("page")) if user_input.get("page") is not None else 1
        all_users = self.user_manager.get_users_info(usernames=usernames, limit=params["limit"], skip=(page-1)*params["limit"],sort_key=params["sort_by"],order=params["order"])
        pages = len(usernames) // params["limit"] + (len(usernames) % params["limit"] > 0) if params["limit"] > 0 else 1

        return self.template_helper.render("admin/admin_users.html", all_users=all_users,
                                           number_of_pages=pages, page_number=page, old_params=params, displayed_selection=json.dumps(params))


class AdministrationUserActionPage(INGIniousAdministratorPage):
    """Action on User Admin page."""

    def POST_AUTH(self, *args, **kwargs):
        username = request.form.get("username")
        action = request.form.get("action")
        feedback = None
        if action == "activate":
            activate_hash = self.user_manager.get_user_activate_hash(username)
            if not self.user_manager.activate_user(activate_hash):
                feedback = _("User not found")
        elif action == "delete":
            if not self.user_manager.delete_user(username):
                feedback = _("Impossible to delete this user")
        elif action == "get_bindings":
            user_info = self.user_manager.get_user_info(username)
            return jsonify(user_info.bindings if user_info is not None else {})
        elif action == "revoke_binding":
            binding_id = request.form.get("binding_id")
            error, feedback = self.user_manager.revoke_binding(username, binding_id)
        elif action == "add_user":
            realname = request.form.get("realname")
            email = request.form.get("email")
            password = request.form.get("password")
            feedback = self.user_manager.create_user({
                "username": username,
                "realname": realname,
                "email": email,
                "password": password,
                "bindings": {},
                "language": "en"})
        else:
            feedback = _("Unknown action.")
        if feedback:
            return jsonify({"error": True, "message": feedback})
        return jsonify({"message": ""})
