# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Profile page """
import web
import hashlib
from pymongo import ReturnDocument

from inginious.frontend.webapp.pages.utils import INGIniousAuthPage


class ProfilePage(INGIniousAuthPage):
    """ Profile page for DB-authenticated users"""

    def save_profile(self, userdata, data):
        """ Save user profile modifications """
        result = userdata
        error = False
        msg = ""

        # Check input format
        if self.app.allow_registration and len(data["oldpasswd"]) > 0 and len(data["passwd"]) < 6:
            error = True
            msg = "Password too short."
        elif self.app.allow_registration and len(data["oldpasswd"]) > 0 and data["passwd"] != data["passwd2"]:
            error = True
            msg = "Passwords don't match !"
        elif self.app.allow_registration and len(data["oldpasswd"]) > 0:
            oldpasswd_hash = hashlib.sha512(data["oldpasswd"].encode("utf-8")).hexdigest()
            passwd_hash = hashlib.sha512(data["passwd"].encode("utf-8")).hexdigest()

            match = {"username": self.user_manager.session_username()}
            if "password" in userdata:
                match["password"] = oldpasswd_hash

            result = self.database.users.find_one_and_update(match,
                                                             {"$set": {
                                                                 "password": passwd_hash,
                                                                 "realname": data["realname"]}
                                                             },
                                                             return_document=ReturnDocument.AFTER)
            if not result:
                error = True
                msg = "Incorrect old password."
            else:
                msg = "Profile updated."
        elif not userdata["username"] and "username" in data:
            found_user = self.database.users.find_one({"username": data["username"]})
            if found_user:
                error = True
                msg = "Username already taken"
            else:
                result = self.database.users.find_one_and_update({"email": userdata["email"]},
                                                                 {"$set": {"username": data["username"]}},
                                                                 return_document=ReturnDocument.AFTER)
                if not result:
                    error = True
                    msg = "Incorrect email."
                else:
                    self.user_manager.connect_user(result["username"], result["realname"], result["email"])
                    msg = "Profile updated."

        else:
            result = self.database.users.find_one_and_update({"username": self.user_manager.session_username()},
                                                             {"$set": {"realname": data["realname"]}},
                                                             return_document=ReturnDocument.AFTER)
            if not result:
                error = True
                msg = "Incorrect username."
            else:
                self.user_manager.set_session_realname(data["realname"])
                msg = "Profile updated."

        return result, msg, error

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """ GET request """
        userdata = self.database.users.find_one({"email": self.user_manager.session_email()})

        if not userdata:
            raise web.notfound()

        return self.template_helper.get_renderer().preferences.profile("", False)

    def POST_AUTH(self):  # pylint: disable=arguments-differ
        """ POST request """
        userdata = self.database.users.find_one({"email": self.user_manager.session_email()})

        if not userdata:
            raise web.notfound()

        msg = ""
        error = False
        data = web.input()
        if "save" in data:
            userdata, msg, error = self.save_profile(userdata, data)

        return self.template_helper.get_renderer().preferences.profile(msg, error)