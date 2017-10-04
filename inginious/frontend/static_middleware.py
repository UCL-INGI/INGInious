# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A middleware for Web.py that serves static content """
import os
import posixpath
import urllib.request, urllib.parse, urllib.error

import web


class StaticApp(web.httpserver.StaticApp, object):
    """WSGI application for serving static files."""

    def __init__(self, base_path, environ, start_response):
        self.base_path = base_path
        super(StaticApp, self).__init__(environ, start_response)

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = [_f for _f in words if _f]
        path = self.base_path
        for word in words:
            _, word = os.path.splitdrive(word)
            _, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'
        return path


class StaticMiddleware(object):
    """ WSGI middleware for serving static files. """

    def __init__(self, app, paths):
        self.app = app
        self.paths = paths

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        path = self.normpath(path)

        for prefix, root_path in self.paths:
            if path.startswith(prefix):
                environ["PATH_INFO"] = web.lstrips(path, prefix)
                return StaticApp(root_path, environ, start_response)
        return self.app(environ, start_response)

    def normpath(self, path):
        """ Normalize the path """
        path2 = posixpath.normpath(urllib.parse.unquote(path))
        if path.endswith("/"):
            path2 += "/"
        return path2
