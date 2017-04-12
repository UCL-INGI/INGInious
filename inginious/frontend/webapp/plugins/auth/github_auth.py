# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Github auth plugin """

import os
import web
import json

from inginious.frontend.webapp.pages.utils import INGIniousPage
from inginious.frontend.webapp.user_manager import AuthMethod
from requests_oauthlib import OAuth2Session


client_id = ''
client_secret = ''

authorization_base_url = 'https://github.com/login/oauth/authorize?scope=user:email'
token_url = 'https://github.com/login/oauth/access_token'

class GithubAuthMethod(AuthMethod):
    """
    Github auth method
    """

    def __init__(self, name, link):
        self._name = name
        self._link = link

    def get_name(self):
        return self._name

    def get_link(self):
        return self._link


class AuthenticationPage(INGIniousPage):
    def GET(self):
        github = OAuth2Session(client_id)
        authorization_url, state = github.authorization_url(authorization_base_url)
        self.user_manager._session['oauth_state'] = state
        self.user_manager._session['redir_url'] = web.ctx.env.get('HTTP_REFERER','/').rsplit("?logoff")[0]
        raise web.seeother(authorization_url)


class CallbackPage(INGIniousPage):
    def GET(self):
        github = OAuth2Session(client_id, state=self.user_manager._session['oauth_state'])
        try:
            github.fetch_token(token_url, client_secret=client_secret, authorization_response=web.ctx.home + web.ctx.fullpath)
            r = github.get('https://api.github.com/user')
            profile = json.loads(r.content.decode('utf-8'))
            r = github.get('https://api.github.com/user/emails')
            profile["email"] = json.loads(r.content.decode('utf-8'))[0]["email"]
            self.user_manager.end_auth((str(profile["id"]), profile["name"], profile["email"]), web.ctx['ip'])
        except:
            raise web.seeother("/")

        raise web.seeother(self.user_manager._session["redir_url"])


def init(plugin_manager, course_factory, client, conf):
    global client_id, client_secret

    if conf.get("debug", False):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    client_id = conf.get("client_id", "")
    client_secret = conf.get("client_secret", "")

    plugin_manager.add_page('/auth/github-callback', CallbackPage)
    plugin_manager.add_page('/auth/github', AuthenticationPage)
    plugin_manager.register_auth_method(GithubAuthMethod(conf.get('name', 'Github Login'), "/auth/github"))
