# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

import flask

import jwt
from datetime import datetime

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage

class CourseAPITokens(INGIniousAdminPage):
    """ List information about api tokens """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def POST_AUTH(self, courseid):
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)
        user_input = flask.request.form.copy()
        username = self.user_manager.session_username()

        if "add_token" in user_input:
            descr = user_input.get("descr", "")
            expire = user_input.get("expiration", "")
            if expire == "":
                expire = "no"
            insert_id = self.database.tokens.insert_one({"courseid": courseid, "expire": str(expire), "description": descr, "username": username}).inserted_id
            msg = str(self.GET_TOKEN(str(insert_id), courseid, username, expire))

        else:
            tok_id = user_input.get("token_id", "")
            self.database.tokens.delete_one({"$expr": {"$eq": ["$_id", {"$toObjectId": tok_id}]}, "username": username})
            msg = "removed"

        return self.page(course, msg)

    def GET_TOKEN(self, insert_id, courseid, username, expire):
        """ Give a token """
        key = "secret" # this is a test, needs change
        if expire == "no":
            encoded = jwt.encode({"id": insert_id, "course": courseid, "username": username}, key, algorithm="HS256")
        else:
            encoded = jwt.encode({"id": insert_id, "course": courseid, "username": username, "expire": expire}, key, algorithm="HS256")
        return encoded

    def page(self, course, msg=""):
        """ Display the page """
        tokens = self.database.tokens.find({"username": self.user_manager.session_username()})
        now = str(datetime.now())
        return self.template_helper.render("course_admin/api_tokens.html", course=course, msg=msg, tokens=tokens, now=now)
