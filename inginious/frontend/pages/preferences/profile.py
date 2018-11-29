# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Profile page """
import hashlib
import re
import web
from pymongo import ReturnDocument

from inginious.frontend.pages.utils import INGIniousAuthPage


class ProfilePage(INGIniousAuthPage):
    """ Profile page for DB-authenticated users"""

    def save_profile(self, userdata, data):
        """ Save user profile modifications """
        result = userdata
        error = False

        # Check if updating username.
        if not userdata["username"] and "username" in data:
            if re.match(r"^[-_|~0-9A-Z]{4,}$", data["username"], re.IGNORECASE) is None:
                error = True
                msg = _("Invalid username format.")
            elif self.database.users.find_one({"username": data["username"]}):
                error = True
                msg = _("Username already taken")
            else:
                result = self.database.users.find_one_and_update({"email": userdata["email"]},
                                                                 {"$set": {"username": data["username"]}},
                                                                 return_document=ReturnDocument.AFTER)
                if not result:
                    error = True
                    msg = _("Incorrect email.")
                else:
                    self.user_manager.connect_user(result["username"], result["realname"], result["email"],
                                                   result["language"])
                    msg = _("Profile updated.")
            return result, msg, error

        # Check if updating the password.
        if self.app.allow_registration and len(data["passwd"]) in range(1, 6):
            error = True
            msg = _("Password too short.")
            return result, msg, error
        elif self.app.allow_registration and len(data["passwd"]) > 0 and data["passwd"] != data["passwd2"]:
            error = True
            msg = _("Passwords don't match !")
            return result, msg, error
        elif self.app.allow_registration and len(data["passwd"]) >= 6:
            oldpasswd_hash = hashlib.sha512(data["oldpasswd"].encode("utf-8")).hexdigest()
            passwd_hash = hashlib.sha512(data["passwd"].encode("utf-8")).hexdigest()

            match = {"username": self.user_manager.session_username()}
            if "password" in userdata:
                match["password"] = oldpasswd_hash

            result = self.database.users.find_one_and_update(match,
                                                             {"$set": {"password": passwd_hash}},
                                                             return_document=ReturnDocument.AFTER)
            if not result:
                error = True
                msg = _("Incorrect old password.")
                return result, msg, error

        # Check if updating language
        if data["language"] != userdata["language"]:
            language = data["language"] if data["language"] in self.app.available_languages else "en"
            result = self.database.users.find_one_and_update({"username": self.user_manager.session_username()},
                                                             {"$set": {"language": language}},
                                                             return_document=ReturnDocument.AFTER)
            if not result:
                error = True
                msg = _("Incorrect username.")
                return result, msg, error
            else:
                self.user_manager.set_session_language(language)

        # Checks if updating name
        if len(data["realname"]) > 0:
            result = self.database.users.find_one_and_update({"username": self.user_manager.session_username()},
                                                             {"$set": {"realname": data["realname"]}},
                                                             return_document=ReturnDocument.AFTER)
            if not result:
                error = True
                msg = _("Incorrect username.")
                return result, msg, error
            else:
                self.user_manager.set_session_realname(data["realname"])
        else:
            error = True
            msg = _("Name is too short.")
            return result, msg, error

        msg = _("Profile updated.")
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
