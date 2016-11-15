# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

"""
Custom Session Management
Initial code taken from web.py (public domain)
"""

import os, time
import os.path
from copy import deepcopy
import hashlib
from web import utils
import web


class CustomSession(object):
    """Session management made via URL. It is a bit different from the default one: you have to call load() manually."""
    __slots__ = [
        "store", "_initializer", "_last_cleanup_time", "_config", "_data",
        "__getitem__", "__setitem__", "__delitem__"
    ]

    def __init__(self, app, store, initializer=None):
        self.store = store
        self._initializer = initializer
        self._last_cleanup_time = 0
        self._config = utils.storage(web.config.session_parameters)
        self._data = utils.threadeddict()
        self._data["session_id"] = None

        if app:
            app.add_processor(self._processor)

        self.__getitem__ = self._data.__getitem__
        self.__setitem__ = self._data.__setitem__
        self.__delitem__ = self._data.__delitem__

    def __contains__(self, name):
        return name in self._data

    def __getattr__(self, name):
        return getattr(self._data, name)

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            setattr(self._data, name, value)

    def __delattr__(self, name):
        delattr(self._data, name)

    def _processor(self, handler):
        """Application processor to setup session for every request"""
        self._cleanup()

        try:
            return handler()
        finally:
            self._save()

    def load(self, session_id):
        """Load the session from the store, by the id given as parameter"""
        self._data["session_id"] = session_id

        # protection against session_id tampering
        if self._data["session_id"] and not self._valid_session_id(self._data["session_id"]):
            self._data["session_id"] = None

        self._check_expiry()
        if self._data["session_id"]:
            d = self.store[self._data["session_id"]]
            self.update(d)

        if not self._data["session_id"]:
            self._data["session_id"] = self._generate_session_id()

            if self._initializer:
                if isinstance(self._initializer, dict):
                    self.update(deepcopy(self._initializer))
                elif hasattr(self._initializer, '__call__'):
                    self._initializer()

        self._data["ip"] = web.ctx.ip

    def _check_expiry(self):
        # check for expiry
        if self._data["session_id"] and self._data["session_id"] not in self.store:
            self._data["session_id"] = None

    def _save(self):
        if not self._data.get('_killed') and self._data["session_id"] is not None:
            self.store[self._data["session_id"]] = dict(self._data)

    def _generate_session_id(self):
        """Generate a random id for session"""

        while True:
            rand = os.urandom(16)
            now = time.time()
            secret_key = self._config.secret_key
            session_id = hashlib.sha1(("%s%s%s%s" % (rand, now, utils.safestr(web.ctx.ip), secret_key)).encode("utf-8"))
            session_id = session_id.hexdigest()
            if session_id not in self.store:
                break
        return session_id

    def _valid_session_id(self, session_id):
        rx = utils.re_compile('^[0-9a-fA-F]+$')
        return rx.match(session_id)

    def _cleanup(self):
        """Cleanup the stored sessions"""
        self._data["session_id"] = None
        current_time = time.time()
        timeout = self._config.timeout
        if current_time - self._last_cleanup_time > timeout:
            self.store.cleanup(timeout)
            self._last_cleanup_time = current_time

    def kill(self):
        """Kill the session, make it no longer available"""
        del self.store[self._data["session_id"]]
        self._data["_killed"] = True
