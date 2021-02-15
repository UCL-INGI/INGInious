from flask import session, redirect, url_for
from flask.views import MethodView


class HelloView(MethodView):
    def get(self, sessionid):
        if not sessionid and session.get("cookieless", False):
            return redirect(url_for("helloview", sessionid=session.get("session_id")))

        return 'Hello from Flask {}, with sessionid {}!'.format(str(session.get("realname", "anonymous")), session.get("session_id", None))

    def post(self, sessionid):
        return 'Hello from Flask {}, with sessionid {}!'.format(str(session.get("realname", "anonymous")), session.get("session_id", None))