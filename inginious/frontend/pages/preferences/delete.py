# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Profile page """
import flask
from flask import redirect
from werkzeug.exceptions import Forbidden

from inginious.frontend.pages.utils import INGIniousAuthPage


class DeletePage(INGIniousAuthPage):
    """ Delete account page for DB-authenticated users"""

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
            msg = _("The specified email is incorrect.")
        else:
            self.database.submissions.remove({"username": username})
            self.database.user_tasks.remove({"username": username})

            all_courses = self.course_factory.get_all_courses()

            for courseid, course in all_courses.items():
                if self.user_manager.course_is_open_to_user(course, username):
                    self.user_manager.course_unregister_user(course, username)

            self.user_manager.disconnect_user()

        return msg, error

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """ GET request """
        userdata = self.database.users.find_one({"username": self.user_manager.session_username()})

        if not userdata or not self.app.allow_deletion:
            raise Forbidden(description=_("User unavailable or deletion is forbidden."))

        return self.template_helper.render("preferences/delete.html", msg="", error=False)

    def POST_AUTH(self):  # pylint: disable=arguments-differ
        """ POST request """
        userdata = self.database.users.find_one({"username": self.user_manager.session_username()})

        if not userdata or not self.app.allow_deletion:
            raise Forbidden(description=_("User unavailable or deletion forbidden."))

        msg = ""
        error = False
        data = flask.request.form
        if "delete" in data:
            msg, error = self.delete_account(data)
            if not error:
                return redirect("/index")

        return self.template_helper.render("preferences/delete.html", msg=msg, error=error)
