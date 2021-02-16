# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from flask import session, redirect, url_for, current_app
from flask.views import MethodView

from werkzeug.exceptions import InternalServerError

class HelloView(MethodView):
    def get(self, sessionid):
        if not sessionid and session.get("cookieless", False):
            return redirect(url_for("helloview", sessionid=session.get("session_id")))

        user_manager = current_app.user_manager

        return current_app.template_helper.render("static.html",
                                                  title="test",
                                                  content="<h2>Hello from Flask!</h2>You are {}, {}, with sessionid {}!".format(
                                                      user_manager.session_realname(),
                                                      user_manager.session_email(),
                                                      session.get("session_id", None))
                                                  )

    def post(self, sessionid):
        user_manager = current_app.user_manager
        return 'Hello from Flask {}, {}, with sessionid {}!'.format(
            user_manager.session_realname(),
            user_manager.session_email(),
            session.get("session_id", None))