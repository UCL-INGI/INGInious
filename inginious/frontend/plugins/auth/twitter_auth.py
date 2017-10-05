# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Facebook auth plugin """

import json
import os
import web
from requests_oauthlib import OAuth1Session

from inginious.frontend.user_manager import AuthMethod

request_token_url = "https://api.twitter.com/oauth/request_token"
authorization_base_url = 'https://api.twitter.com/oauth/authorize'
access_token_url = 'https://api.twitter.com/oauth/access_token'


class TwitterAuthMethod(AuthMethod):
    """
    Twitter auth method
    """
    def get_auth_link(self, user_manager):
        twitter = OAuth1Session(self._client_id, client_secret=self._client_secret,
                                callback_uri=web.ctx.home + self._callback_page)
        twitter.fetch_request_token(request_token_url)
        authorization_url = twitter.authorization_url(authorization_base_url)
        return authorization_url

    def callback(self, user_manager):
        twitter = OAuth1Session(self._client_id, client_secret=self._client_secret,
                                callback_uri=web.ctx.home + self._callback_page)
        try:
            twitter.parse_authorization_response(web.ctx.home + web.ctx.fullpath)
            twitter.fetch_access_token(access_token_url)
            r = twitter.get('https://api.twitter.com/1.1/account/verify_credentials.json?include_email=true')
            profile = json.loads(r.content.decode('utf-8'))
            return str(profile["id"]), profile["name"], profile["email"]
        except:
            return None

    def get_id(self):
        return self._id

    def __init__(self, id, name, client_id, client_secret):
        self._id = id
        self._name = name
        self._client_id = client_id
        self._client_secret = client_secret
        self._callback_page = '/auth/' + self._id + '/callback'

    def get_name(self):
        return self._name

    def get_imlink(self):
        return '<i class="fa fa-twitter-square" style="font-size:50px; color:#00abf1;"></i>'


def init(plugin_manager, course_factory, client, conf):

    if conf.get("debug", False):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    client_id = conf.get("client_id", "")
    client_secret = conf.get("client_secret", "")

    plugin_manager.register_auth_method(TwitterAuthMethod(conf.get("id"), conf.get('name', 'Twitter Login'), client_id, client_secret))
