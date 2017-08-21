# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os, time
import os.path
from copy import deepcopy
import hashlib
from web import utils
import web
from web.session import SessionExpired


class CookieLessCompatibleApplication(web.application):
    def __init__(self, session_storage):
        """
        :param session_storage: a Storage object, where sessions will be saved
        """
        super(CookieLessCompatibleApplication, self).__init__((), globals(), autoreload=False)
        self._session = CookieLessCompatibleSession(self, session_storage)

    def get_session(self):
        return self._session

    def init_mapping(self, mapping):
        self.mapping = [(r"(/@[a-f0-9A-F_]*@)?" +a, b) for a,b in utils.group(mapping, 2)]

    def add_mapping(self, pattern, classname):
        self.mapping.append((r"(/@[a-f0-9A-F_]*@)?" + pattern, classname))
    
    def _delegate(self, f, fvars, args=None):
        if args is None:
            args = [None]

        # load session
        if args[0] == "/@@":
            self._session.load('') # creates a new session
            raise web.redirect("/@" + self._session.session_id + "@"+web.ctx.fullpath[3:]) # redirect to the same page, with the new
            # session id
        elif args[0] is None:
            self._session.load(None)
        else:
            self._session.load(args[0][2:len(args[0])-1])

        return super(CookieLessCompatibleApplication, self)._delegate(f, fvars, args[1:])

    def get_homepath(self, ignore_session=False, force_cookieless=False):
        """
        :param ignore_session: Ignore the cookieless session_id that should be put in the URL
        :param force_cookieless: Force the cookieless session; the link will include the session_creator if needed.
        """
        if not ignore_session and self._session.get("session_id") is not None and self._session.get("cookieless", False):
            return web.ctx.homepath + "/@" + self._session.get("session_id") + "@"
        elif not ignore_session and force_cookieless:
            return web.ctx.homepath + "/@@"
        else:
            return web.ctx.homepath


class CookieLessCompatibleSession(object):
    """ A session that can either store its session id in a Cookie or directly in the webpage URL. 
        The load(session_id) function must be called manually, in order for the session to be loaded. 
        This is usually done by the CookieLessCompatibleApplication.
        
        Original code from web.py (public domain)
    """

    __slots__ = [
        "store", "_initializer", "_last_cleanup_time", "_config", "_data", "_session_id_regex",
        "__getitem__", "__setitem__", "__delitem__"
    ]

    def __init__(self, app, store, initializer=None):
        self.store = store
        self._initializer = initializer
        self._last_cleanup_time = 0
        self._config = utils.storage(web.config.session_parameters)
        self._data = utils.threadeddict()
        self._session_id_regex = utils.re_compile('^[0-9a-fA-F]+$')

        self.__getitem__ = self._data.__getitem__
        self.__setitem__ = self._data.__setitem__
        self.__delitem__ = self._data.__delitem__

        if app:
            app.add_processor(self._processor)

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
            self.save()

    def load(self, session_id=None):
        """ Load the session from the store.
        session_id can be:
        - None: load from cookie
        - '': create a new cookieless session_id
        - a string which is the session_id to be used.
        """

        if session_id is None:
            cookie_name = self._config.cookie_name
            self._data["session_id"] = web.cookies().get(cookie_name)
            self._data["cookieless"] = False
        else:
            if session_id == '':
                self._data["session_id"] = None  # will be created
            else:
                self._data["session_id"] = session_id
            self._data["cookieless"] = True

        # protection against session_id tampering
        if self._data["session_id"] and not self._valid_session_id(self._data["session_id"]):
            self._data["session_id"] = None

        self._check_expiry()
        if self._data["session_id"]:
            d = self.store[self._data["session_id"]]
            self.update(d)
            self._validate_ip()

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
            if self._config.ignore_expiry:
                self._data["session_id"] = None
            else:
                return self.expired()

    def _validate_ip(self):
        # check for change of IP
        if self._data["session_id"] and self.get('ip', None) != web.ctx.ip:
            if not self._config.ignore_change_ip or self._data["cookieless"] is True:
                return self.expired()

    def _save_cookieless(self):
        if not self._data.get('_killed') and self._data["session_id"] is not None:
            self.store[self._data["session_id"]] = dict(self._data)

    def _save_cookie(self):
        if not self.get('_killed'):
            self._setcookie(self._data["session_id"])
            self.store[self._data["session_id"]] = dict(self._data)
        else:
            self._setcookie(self._data["session_id"], expires=-1)

    def save(self):
        if self._data.get("cookieless", False):
            self._save_cookieless()
        else:
            self._save_cookie()

    def _setcookie(self, session_id, expires='', **kw):
        cookie_name = self._config.cookie_name
        cookie_domain = self._config.cookie_domain
        cookie_path = self._config.cookie_path
        httponly = self._config.httponly
        secure = self._config.secure
        web.setcookie(cookie_name, session_id, expires=expires, domain=cookie_domain, httponly=httponly, secure=secure, path=cookie_path)

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
        return self._session_id_regex.match(session_id)

    def _cleanup(self):
        """Cleanup the stored sessions"""
        current_time = time.time()
        timeout = self._config.timeout
        if current_time - self._last_cleanup_time > timeout:
            self.store.cleanup(timeout)
            self._last_cleanup_time = current_time

    def expired(self):
        """Called when an expired session is atime"""
        self._data["_killed"] = True
        self.save()
        raise SessionExpired(self._config.expired_message)

    def kill(self):
        """Kill the session, make it no longer available"""
        del self.store[self.session_id]
        self._data["_killed"] = True
