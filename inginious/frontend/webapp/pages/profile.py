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

        return self.template_helper.get_renderer().profile("", False, True)

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

        return self.template_helper.get_renderer().profile(msg, error, True)