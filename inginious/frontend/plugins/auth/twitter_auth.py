# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Facebook auth plugin """

import json
import os
import flask

from requests_oauthlib import OAuth1Session

from inginious.frontend.user_manager import AuthMethod

request_token_url = "https://api.twitter.com/oauth/request_token"
authorization_base_url = 'https://api.twitter.com/oauth/authorize'
access_token_url = 'https://api.twitter.com/oauth/access_token'


class TwitterAuthMethod(AuthMethod):
    """
    Twitter auth method
    """
    def get_auth_link(self, auth_storage, share=False):
        client_id = self._share_client_id if share else self._client_id
        client_secret = self._clients[client_id]
        twitter = OAuth1Session(client_id, client_secret=client_secret,
                                callback_uri=flask.request.url_root + self._callback_page)
        twitter.fetch_request_token(request_token_url)
        authorization_url = twitter.authorization_url(authorization_base_url)
        auth_storage["oauth_client_id"] = client_id
        return authorization_url

    def callback(self, auth_storage):
        client_id = auth_storage.get("oauth_client_id", self._client_id)
        client_secret = self._clients[client_id]
        twitter = OAuth1Session(client_id, client_secret=client_secret,
                                callback_uri=flask.request.url_root + self._callback_page)
        try:
            twitter.parse_authorization_response(flask.request.url)
            twitter.fetch_access_token(access_token_url)
            r = twitter.get('https://api.twitter.com/1.1/account/verify_credentials.json?include_email=true')
            profile = json.loads(r.content.decode('utf-8'))
            auth_storage["session"] = twitter
            return str(profile["id"]), profile["name"], profile["email"], {}
        except:
            return None

    def share(self, auth_storage, course, task, submission, language):
        twitter = auth_storage.get("session", None)
        if twitter:
            r = twitter.post(
                "https://api.twitter.com/1.1/statuses/update.json",
                {"status": _("Check out INGInious course {course} and beat my score of {score}% on task {task} !").format(
                    course=course.get_name(language),
                    task=task.get_name(language),
                    score=submission["grade"]
                ) + " " + flask.request.url_root + "course/" + course.get_id() + "/" + task.get_id() + " #inginious" + ((" via @" + self._twitter_user) if self._twitter_user else "")
                 }
            )
            result = json.loads(r.content.decode('utf-8'))
            return "id" in result

    def allow_share(self):
        return True

    def get_id(self):
        return self._id

    def __init__(self, id, name, client_id, client_secret, share_client_id, share_client_secret, twitter_user):
        self._id = id
        self._name = name
        self._client_id = client_id
        self._client_secret = client_secret
        self._share_client_id = share_client_id
        self._share_client_secret = share_client_secret
        self._clients = {self._client_id: self._client_secret, self._share_client_id: self._share_client_secret}
        self._callback_page = 'auth/callback/' + self._id
        self._twitter_user = twitter_user

    def get_name(self):
        return self._name

    def get_imlink(self):
        return '<i class="fa fa-twitter-square" style="font-size:50px; color:#00abf1;"></i>'


def init(plugin_manager, course_factory, client, conf):

    if conf.get("debug", False):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    client_id = conf.get("client_id", "")
    client_secret = conf.get("client_secret", "")
    share_client_id = conf.get("share_client_id", client_id)
    share_client_secret = conf.get("share_client_secret", client_secret)
    twitter_user = conf.get("user", "")

    plugin_manager.register_auth_method(TwitterAuthMethod(conf.get("id"), conf.get('name', 'Twitter'),
                                                          client_id, client_secret,
                                                          share_client_id, share_client_secret, twitter_user))
