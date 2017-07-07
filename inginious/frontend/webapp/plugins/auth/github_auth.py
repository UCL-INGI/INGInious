# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Github auth plugin """

import os
import web
import json

from inginious.frontend.webapp.user_manager import AuthMethod
from requests_oauthlib import OAuth2Session

authorization_base_url = 'https://github.com/login/oauth/authorize?scope=user:email'
token_url = 'https://github.com/login/oauth/access_token'


class GithubAuthMethod(AuthMethod):
    """
    Github auth method
    """
    def get_auth_link(self, user_manager):
        github = OAuth2Session(self._client_id)
        authorization_url, state = github.authorization_url(authorization_base_url)
        user_manager.set_session_oauth_state(state)
        return authorization_url

    def callback(self, user_manager):
        github = OAuth2Session(self._client_id, state=user_manager.session_oauth_state())
        try:
            github.fetch_token(token_url, client_secret=self._client_secret,
                               authorization_response=web.ctx.home + web.ctx.fullpath)
            r = github.get('https://api.github.com/user')
            profile = json.loads(r.content.decode('utf-8'))
            r = github.get('https://api.github.com/user/emails')
            profile["email"] = json.loads(r.content.decode('utf-8'))[0]["email"]
            return str(profile["id"]), profile["name"], profile["email"]
        except:
            return None

    def __init__(self, id, name, client_id, client_secret):
        self._name = name
        self._id = id
        self._client_id = client_id
        self._client_secret = client_secret

    def get_id(self):
        return self._id

    def get_name(self):
        return self._name

    def get_imlink(self):
        return '<i class="fa fa-github" style="font-size:50px; color:#24292e;"></i>'


def init(plugin_manager, course_factory, client, conf):

    if conf.get("debug", False):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    client_id = conf.get("client_id", "")
    client_secret = conf.get("client_secret", "")

    plugin_manager.register_auth_method(GithubAuthMethod(conf.get("id"), conf.get('name', 'Github Login'), client_id, client_secret))
