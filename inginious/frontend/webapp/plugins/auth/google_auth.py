# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Google auth plugin """

import web
import json
import os

from inginious.frontend.webapp.user_manager import AuthMethod
from requests_oauthlib import OAuth2Session

authorization_base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
token_url = 'https://www.googleapis.com/oauth2/v4/token'
scope = [
    "email",
    "profile"
]

class GoogleAuthMethod(AuthMethod):
    """
    Google auth method
    """

    def get_auth_link(self, user_manager):
        google = OAuth2Session(self._client_id, scope=scope,
            redirect_uri=web.ctx.home + self._callback_page)

        authorization_parameters = {}
        if self._domain != "":
            authorization_parameters["hd"] = self._domain

        authorization_url, state = google.authorization_url(authorization_base_url,
            **authorization_parameters)
        user_manager.set_session_oauth_state(state)
        return authorization_url

    def callback(self, user_manager):
        google = OAuth2Session(self._client_id, state=user_manager.session_oauth_state(),
            redirect_uri=web.ctx.home + self._callback_page, scope=scope)

        try:
            google.fetch_token(token_url, client_secret=self._client_secret,
                authorization_response=web.ctx.home + web.ctx.fullpath)

            response = google.get('https://www.googleapis.com/plus/v1/people/me/openIdConnect')
            profile = json.loads(response.content.decode('utf-8'))

            if self._domain != "":
                print(profile)
                actual_domain = profile["hd"]

                if actual_domain != self._domain:
                    return None

            return str(profile["sub"]), profile["name"], profile["email"]
        except Exception as e:
            return None

    def get_id(self):
        return self._id

    def __init__(self, id, name, client_id, client_secret, domain):
        self._id = id
        self._name = name
        self._client_id = client_id
        self._client_secret = client_secret
        self._callback_page = '/auth/' + self._id + '/callback'
        self._domain = domain

    def get_name(self):
        return self._name

    def get_imlink(self):
        return '<img src="static/common/icons/google-icon.svg" style="height: 50px;">'


def init(plugin_manager, course_factory, client, conf):
    if conf.get("debug", False):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    client_id = conf.get("client_id", "")
    client_secret = conf.get("client_secret", "")
    domain = conf.get("domain", "")

    plugin_manager.register_auth_method(GoogleAuthMethod(conf.get("id"),
        conf.get('name', 'Google Login'), client_id, client_secret, domain))
