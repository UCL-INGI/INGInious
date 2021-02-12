# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

# This code is based on Flask-Session, copyright (c) 2014 by Shipeng Feng.
# https://flasksession.readthedocs.io/

import base64
from uuid import uuid4
from datetime import datetime
from bson.binary import Binary, USER_DEFINED_SUBTYPE
from bson.objectid import ObjectId
from typing import Pattern

try:
    import cPickle as pickle
except ImportError:
    import pickle

from itsdangerous import Signer, BadSignature, want_bytes
from flask.sessions import SessionMixin
from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionInterface


# This class is defined at least for migration
class WebPyLikeSerializer:
    _valid_key_types = {str}
    _atomic_types = {bool, int, float, str, bytes, type(None), Pattern, datetime}

    def _needs_encode(self, obj):
        obtype = type(obj)
        if obtype in self._atomic_types:
            return False
        if obtype is list:
            return any(self._needs_encode(i) for i in obj)
        if obtype is dict:
            return any(type(k) not in self._valid_key_types or self._needs_encode(v)
                       for (k, v) in obj.items())
        return True

    def encode(self, session_dict):
        """encodes session dict as a string"""
        pickled = pickle.dumps(session_dict)
        return base64.encodebytes(pickled)

    def decode(self, session_data):
        """decodes the data to get back the session dict """
        pickled = base64.decodebytes(session_data)
        return pickle.loads(pickled)

    def loads(self, data):
        return dict((k, self.decode(self, v) if isinstance(v, Binary) and v.subtype == USER_DEFINED_SUBTYPE else v)
                    for (k, v) in data.items())

    def dumps(self, sessiondict):
        return dict((k, Binary(self.encode(self, v), USER_DEFINED_SUBTYPE) if self._needs_encode(v) else v)
                    for (k, v) in sessiondict.items())


class MongoDBSession(CallbackDict, SessionMixin):
    """Baseclass for server-side based sessions."""

    def __init__(self, initial=None, sid=None, permanent=None):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        if permanent:
            self.permanent = permanent
        self.modified = False

        self['session_id'] = sid
        self['cookieless'] = False


class MongoDBSessionInterface(SessionInterface):
    """A Session interface that uses mongodb as backend.
    :param client: A ``pymongo.MongoClient`` instance.
    :param db: The database you want to use.
    :param collection: The collection you want to use.
    :param use_signer: Whether to sign the session id cookie or not.
    :param permanent: Whether to use permanent session or not.
    """

    serializer = WebPyLikeSerializer()
    session_class = MongoDBSession

    def __init__(self, client, db, collection, use_signer=False,
                 permanent=True):
        self.client = client
        self.store = client[db][collection]
        self.use_signer = use_signer
        self.permanent = permanent

    def _generate_sid(self):
        return str(ObjectId())

    def _get_signer(self, app):
        if not app.secret_key:
            return None
        return Signer(app.secret_key, salt='flask-session',
                      key_derivation='hmac')

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self._generate_sid()
            return self.session_class(sid=sid, permanent=self.permanent)
        if self.use_signer:
            signer = self._get_signer(app)
            if signer is None:
                return None
            try:
                sid_as_bytes = signer.unsign(sid)
                sid = sid_as_bytes.decode()
            except BadSignature:
                sid = self._generate_sid()
                return self.session_class(sid=sid, permanent=self.permanent)

        store_id = sid
        document = self.store.find_one({'_id': store_id})
        if document and document.get('expiration') <= datetime.utcnow():
            # Delete expired session
            self.store.remove({'_id': store_id})
            document = None
        if document is not None:
            try:
                val = document['data']
                data = self.serializer.loads(want_bytes(val))
                return self.session_class(data, sid=sid)
            except:
                return self.session_class(sid=sid, permanent=self.permanent)
        return self.session_class(sid=sid, permanent=self.permanent)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        store_id = session.sid
        if not session:
            if session.modified:
                self.store.remove({'_id': store_id})
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain, path=path)
            return

        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        expires = self.get_expiration_time(app, session)
        val = self.serializer.dumps(dict(session))
        self.store.update({'_id': store_id},
                          {'data': val,
                           'expiration': expires}, True)
        if self.use_signer:
            session_id = self._get_signer(app).sign(want_bytes(session.sid))
        else:
            session_id = session.sid
        response.set_cookie(app.session_cookie_name, session_id,
                            expires=expires, httponly=httponly,
                            domain=domain, path=path, secure=secure)