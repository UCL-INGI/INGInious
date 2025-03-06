# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

import flask

import jwt
from datetime import datetime

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage

class CourseAPITokensPage(INGIniousAdminPage):
    """ List information about api tokens """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def POST_AUTH(self, courseid):
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)
        user_input = flask.request.form

        if "add_token" in user_input:
            descr = user_input.get("descr", "")
            expire = user_input.get("expiration", "")
            if expire == "":
                expire = datetime(9999, 12, 31)
            else:
                expire = datetime.strptime(expire, "YYYY-MM-DD HH:mm:ss")
            document = {"courseid": courseid, "expire": expire, "description": descr}
            self.database.tokens.insert_one(document)
            document["_id"] = str(document["_id"]) # otherwise can't be serialized to JSON by jwt
            document["expire"] = str(document["expire"])
            msg = str(self.generate_token(document))

        else:
            tok_id = user_input.get("token_id", "")
            self.database.tokens.delete_one({"$expr": {"$eq": ["$_id", {"$toObjectId": tok_id}]}})
            msg = "removed"

        return self.page(course, msg)

    def generate_token(self, document):
        """ Give a token """
        key = str(self.app.jwt_key)
        encoded = jwt.encode(document, key, algorithm="HS256")
        return encoded

    def page(self, course, msg=""):
        """ Display the page """
        tokens = self.database.tokens.find({"courseid": course.get_id()})
        now = datetime.now()
        return self.template_helper.render("course_admin/api_tokens.html", course=course, msg=msg, tokens=tokens, now=now)
