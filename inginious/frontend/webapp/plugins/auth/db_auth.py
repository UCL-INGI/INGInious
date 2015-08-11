# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Database auth """

import hashlib
import web
import re
from inginious.frontend.webapp.user_manager import AuthMethod
from inginious.frontend.webapp.pages.utils import INGIniousPage


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
        username = login_data["login"]
        password_hash = hashlib.sha512(login_data["password"]).hexdigest()

        user = self._database.users.find_one({"username": username, "password": password_hash, "activate": {"$exists": False}})

        if user is not None:
            return username, user["realname"], user["email"]
        else:
            return None

    def needed_fields(self):
        return {"input": {"login": {"type": "text", "placeholder": "Login"}, "password": {"type": "password", "placeholder": "Password"}},
                "info": """<div class="text-center"><a href="/register">Register</a> - <a href="/register#lostpasswd">Lost password ?</a></div>"""}

    def should_cache(self):
        return False

    def get_users_info(self, usernames):
        """
        :param usernames: a list of usernames
        :return: a dict containing key/pairs {username: (realname, email)} if the user is available with this auth method,
            {username: None} else
        """
        retval = {username: None for username in usernames}
        for username in retval:
            if username in self._users:
                retval[username] = (username, "{}@inginious.org".format(username))
        return retval

class RegistrationPage(INGIniousPage):
        """ Displays the scoreboard of the contest """

        def GET(self):
            error = False
            msg = ""
            data = web.input()

            if "activate" in data:
                user = self.database.users.find_one_and_update({"activate": data["activate"]}, {"$unset": {"activate": True}})
                if user is None:
                    error = True
                    msg = "Invalid activation hash."
                else:
                    msg = "You are now activated. You can proceed to login."

            return self.template_helper.get_custom_template_renderer('frontend/webapp/templates', 'layout').register(msg, error)

        def POST(self):
            error = False
            msg = ""

            data = web.input()

            # Check input format
            if re.match("\w{4,}$", data["username"]) is None:
                error = True
                msg = "Invalid username format."
            elif re.match("(<)?(\w+@\w+(?:\.\w+)+)(?(1)>)", data["email"]) is None:
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
                    passwd_hash = hashlib.sha512(data["passwd"]).hexdigest()
                    activate_hash = hashlib.sha512(data["username"]).hexdigest()
                    self.database.users.insert({"username": data["username"],
                                                "realname": data["realname"],
                                                "email": data["email"],
                                                "password": passwd_hash,
                                                "activate": activate_hash})
                    try:
                        web.sendmail(web.config.smtp_sendername, data["email"], "Welcome on INGInious",
                                 """Welcome on INGInious !

To activate your account, please click on the following link :
""" + web.ctx.homedomain + "/register?activate=" + activate_hash)
                        msg = "You are succesfully registered. An email has been sent to you for activation."
                    except:
                        error = True
                        msg = "Something went wrong while sending you activation email. Please contact the administrator."

            return self.template_helper.get_custom_template_renderer('frontend/webapp/templates', 'layout').register(msg, error)

def init(plugin_manager, _, _2, conf):
    """
        Allow authentication from database
    """

    plugin_manager.register_auth_method(DatabaseAuthMethod(conf.get('name', 'WebApp Database'), plugin_manager.get_database()))
    plugin_manager.add_page('/register', RegistrationPage)
