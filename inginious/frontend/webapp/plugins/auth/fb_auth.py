# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Facebook auth plugin """

import web
import json
import os

from inginious.frontend.webapp.pages.utils import INGIniousPage
from inginious.frontend.webapp.user_manager import AuthMethod
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix


client_id = ""
client_secret = ""
authorization_base_url = 'https://www.facebook.com/dialog/oauth?scope=public_profile,email'
token_url = 'https://graph.facebook.com/oauth/access_token'

class FacebookAuthMethod(AuthMethod):
    """
    Facebook auth method
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
        facebook = OAuth2Session(client_id, redirect_uri=web.ctx.home + "/auth/facebook-callback")
        facebook = facebook_compliance_fix(facebook)
        authorization_url, state = facebook.authorization_url(authorization_base_url)
        self.user_manager._session['oauth_state'] = state
        self.user_manager._session['redir_url'] = web.ctx.env.get('HTTP_REFERER','/').rsplit("?logoff")[0]
        raise web.seeother(authorization_url)


class CallbackPage(INGIniousPage):
    def GET(self):
        facebook = OAuth2Session(client_id, state=self.user_manager._session['oauth_state'], redirect_uri= web.ctx.home + "/auth/facebook-callback")
        try:
            facebook.fetch_token(token_url, client_secret=client_secret, authorization_response=web.ctx.home + web.ctx.fullpath)
            r = facebook.get('https://graph.facebook.com/me?fields=id,name,email')
            profile = json.loads(r.content.decode('utf-8'))
            self.user_manager.end_auth((profile["id"], profile["name"], profile["email"]), web.ctx['ip'])
        except:
            raise web.seeother("/")

        raise web.seeother(self.user_manager._session["redir_url"])


def init(plugin_manager, course_factory, client, conf):
    global client_id, client_secret

    if conf.get("debug", False):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    client_id = conf.get("client_id", "")
    client_secret = conf.get("client_secret", "")

    plugin_manager.add_page('/auth/facebook-callback', CallbackPage)
    plugin_manager.add_page('/auth/facebook', AuthenticationPage)
    plugin_manager.register_auth_method(FacebookAuthMethod(conf.get('name', 'Facebook Login'), "/auth/facebook"))
