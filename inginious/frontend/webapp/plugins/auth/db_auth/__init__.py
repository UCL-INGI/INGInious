# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Database auth """

import hashlib
import random
import re
from collections import OrderedDict

import web

from inginious.frontend.webapp.user_manager import AuthMethod
from inginious.frontend.webapp.pages.utils import INGIniousPage, INGIniousAuthPage
from pymongo.collection import ReturnDocument

allow_deletion = True


class DatabaseAuthMethod(AuthMethod):
    """
    MongoDB Database auth method
    """

    def __init__(self, name, database):
        self._name = name
        self._database = database

    def get_name(self):
        return self._name

    def auth(self, login_data):
        username = login_data["login"].strip()
        password_hash = hashlib.sha512(login_data["password"].encode("utf-8")).hexdigest()

        user = self._database.users.find_one({"username": username, "password": password_hash, "activate": {"$exists": False}})

        if user is not None:
            return username, user["realname"], user["email"]
        else:
            return None

    def needed_fields(self):
        return {
            "input": OrderedDict((
                ("login", {"type": "text", "placeholder": "Login"}),
                ("password", {"type": "password", "placeholder": "Password"}))),
            "info": '<div class="text-center"><a href="' + web.ctx.home +
                    '/register">Register</a> / <a href="' + web.ctx.home +
                    '/register#lostpasswd">Lost password?</a></div>'
        }

    def should_cache(self):
        return False

    def get_users_info(self, usernames):
        """
        :param usernames: a list of usernames
        :return: a dict containing key/pairs {username: (realname, email)} if the user is available with this auth method,
            {username: None} else
        """
        retval = {username: None for username in usernames}
        data = self._database.users.find({"username": {"$in": usernames}})
        for user in data:
            retval[user["username"]] = (user["realname"], user["email"])
        return retval


class RegistrationPage(INGIniousPage):
    """ Registration page for DB authentication """

    def GET(self):
        """ Handles GET request """
        if self.user_manager.session_logged_in():
            raise web.notfound()

        error = False
        reset = None
        msg = ""
        data = web.input()

        if "activate" in data:
            msg, error = self.activate_user(data)
        elif "reset" in data:
            msg, error, reset = self.get_reset_data(data)

        return self.template_helper.get_custom_renderer('frontend/webapp/plugins/auth/db_auth').register(reset, msg, error)

    def get_reset_data(self, data):
        """ Returns the user info to reset """
        error = False
        reset = None
        msg = ""
        user = self.database.users.find_one({"reset": data["reset"]})
        if user is None:
            error = True
            msg = "Invalid reset hash."
        else:
            reset = {"hash": data["reset"], "username": user["username"], "realname": user["realname"]}

        return msg, error, reset

    def activate_user(self, data):
        """ Activates user """
        error = False
        user = self.database.users.find_one_and_update({"activate": data["activate"]}, {"$unset": {"activate": True}})
        if user is None:
            error = True
            msg = "Invalid activation hash."
        else:
            msg = "You are now activated. You can proceed to login."

        return msg, error

    def register_user(self, data):
        """ Parses input and register user """
        error = False
        msg = ""

        email_re = re.compile(
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
            r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain

        # Check input format
        if re.match(r"\w{4,}$", data["username"]) is None:
            error = True
            msg = "Invalid username format."
        elif email_re.match(data["email"]) is None:
            error = True
            msg = "Invalid email format."
        elif len(data["passwd"]) < 6:
            error = True
            msg = "Password too short."
        elif data["passwd"] != data["passwd2"]:
            error = True
            msg = "Passwords don't match !"

        if not error:
            existing_user = self.database.users.find_one({"$or": [{"username": data["username"]}, {"email": data["email"]}]})
            if existing_user is not None:
                error = True
                if existing_user["username"] == data["username"]:
                    msg = "This username is already taken !"
                else:
                    msg = "This email address is already in use !"
            else:
                passwd_hash = hashlib.sha512(data["passwd"].encode("utf-8")).hexdigest()
                activate_hash = hashlib.sha512(str(random.getrandbits(256)).encode("utf-8")).hexdigest()
                self.database.users.insert({"username": data["username"],
                                            "realname": data["realname"],
                                            "email": data["email"],
                                            "password": passwd_hash,
                                            "activate": activate_hash})
                try:
                    web.sendmail(web.config.smtp_sendername, data["email"], "Welcome on INGInious",
                                 """Welcome on INGInious !

To activate your account, please click on the following link :
""" + web.ctx.home + "/register?activate=" + activate_hash)
                    msg = "You are succesfully registered. An email has been sent to you for activation."
                except:
                    error = True
                    msg = "Something went wrong while sending you activation email. Please contact the administrator."

        return msg, error

    def lost_passwd(self, data):
        """ Send a reset link to user to recover its password """
        error = False
        msg = ""

        # Check input format
        email_re = re.compile(
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
            r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
        if email_re.match(data["recovery_email"]) is None:
            error = True
            msg = "Invalid email format."

        if not error:
            reset_hash = hashlib.sha512(str(random.getrandbits(256)).encode("utf-8")).hexdigest()
            user = self.database.users.find_one_and_update({"email": data["recovery_email"]}, {"$set": {"reset": reset_hash}})
            if user is None:
                error = True
                msg = "This email address was not found in database."
            else:
                try:
                    web.sendmail(web.config.smtp_sendername, data["recovery_email"], "INGInious password recovery",
                                 "Dear " + user["realname"] + """,

Someone (probably you) asked to reset your INGInious password. If this was you, please click on the following link :
""" + web.ctx.home + "/register?reset=" + reset_hash)
                    msg = "An email has been sent to you to reset your password."
                except:
                    error = True
                    msg = "Something went wrong while sending you reset email. Please contact the administrator."

        return msg, error

    def reset_passwd(self, data):
        """ Reset the user password """
        error = False
        msg = ""

        # Check input format
        if len(data["passwd"]) < 6:
            error = True
            msg = "Password too short."
        elif data["passwd"] != data["passwd2"]:
            error = True
            msg = "Passwords don't match !"

        if not error:
            passwd_hash = hashlib.sha512(data["passwd"].encode("utf-8")).hexdigest()
            user = self.database.users.find_one_and_update({"reset": data["reset_hash"]},
                                                           {"$set": {"password": passwd_hash}, "$unset": {"reset": True}})
            if user is None:
                error = True
                msg = "Invalid reset hash."
            else:
                msg = "Your password has been successfully changed."

        return msg, error

    def POST(self):
        """ Handles POST request """
        if self.user_manager.session_logged_in():
            raise web.notfound()

        reset = None
        msg = ""
        error = False
        data = web.input()
        if "register" in data:
            msg, error = self.register_user(data)
        elif "lostpasswd" in data:
            msg, error = self.lost_passwd(data)
        elif "resetpasswd" in data:
            msg, error = self.reset_passwd(data)

        return self.template_helper.get_custom_renderer('frontend/webapp/plugins/auth/db_auth').register(reset, msg, error)


class ProfilePage(INGIniousAuthPage):
    """ Profile page for DB-authenticated users"""

    def save_profile(self, userdata, data):
        """ Save user profile modifications """
        result = userdata
        error = False
        msg = ""

        # Check input format
        if len(data["oldpasswd"]) > 0 and len(data["passwd"]) < 6:
            error = True
            msg = "Password too short."
        elif len(data["oldpasswd"]) > 0 and data["passwd"] != data["passwd2"]:
            error = True
            msg = "Passwords don't match !"
        elif len(data["oldpasswd"]) > 0 :
            oldpasswd_hash = hashlib.sha512(data["oldpasswd"].encode("utf-8")).hexdigest()
            passwd_hash = hashlib.sha512(data["passwd"].encode("utf-8")).hexdigest()
            result = self.database.users.find_one_and_update({"username": self.user_manager.session_username(),
                                                              "password": oldpasswd_hash},
                                                             {"$set": {
                                                                 "password": passwd_hash,
                                                                 "realname": data["realname"]}
                                                             },
                                                             return_document=ReturnDocument.AFTER)
            if not result:
                error = True
                msg = "Incorrect old pasword."
            else:
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

    def delete_account(self, data):
        """ Delete account from DB """
        error = False
        msg = ""

        if not allow_deletion:
            return "Not allowed.", True

        username = self.user_manager.session_username()

        # Check input format
        result = self.database.users.find_one_and_delete({"username": username,
                                                          "email": data.get("delete_email", "")})
        if not result:
            error = True
            msg = "The specified email is incorrect."
        else:
            self.database.submissions.remove({"username": username})
            self.database.user_tasks.remove({"username": username})

            all_courses = self.course_factory.get_all_courses()

            for courseid, course in all_courses.items():
                if self.user_manager.course_is_open_to_user(course, username):
                    self.user_manager.course_unregister_user(course, username)

            self.user_manager.disconnect_user(web.ctx['ip'])
            raise web.seeother("/index")

        return msg, error

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """ GET request """
        userdata = self.database.users.find_one({"username": self.user_manager.session_username()})

        if not userdata:
            raise web.notfound()

        return self.template_helper.get_custom_renderer('frontend/webapp/plugins/auth/db_auth').profile("", False, allow_deletion)

    def POST_AUTH(self):  # pylint: disable=arguments-differ
        """ POST request """
        userdata = self.database.users.find_one({"username": self.user_manager.session_username()})

        if not userdata:
            raise web.notfound()

        msg = ""
        error = False
        data = web.input()
        if "save" in data:
            userdata, msg, error = self.save_profile(userdata, data)
        elif "delete" in data:
            msg, error = self.delete_account(data)

        return self.template_helper.get_custom_renderer('frontend/webapp/plugins/auth/db_auth').profile(msg, error, allow_deletion)


def main_menu(template_helper, database):
    """ Returns the additional main menu """
    def is_user_in_db(username):
        return True if database.users.find_one({"username": username}) else False
    return str(template_helper.get_custom_renderer('frontend/webapp/plugins/auth/db_auth', layout=False).main_menu(is_user_in_db))


def init(plugin_manager, _, _2, conf):
    """
        Allow authentication from database
    """
    global allow_deletion

    allow_deletion = conf.get("allow_deletion", False)
    plugin_manager.register_auth_method(DatabaseAuthMethod(conf.get('name', 'WebApp'), plugin_manager.get_database()))
    plugin_manager.add_hook("main_menu", lambda template_helper: main_menu(template_helper, plugin_manager.get_database()))
    plugin_manager.add_page('/register', RegistrationPage)
    plugin_manager.add_page('/profile', ProfilePage)
