# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os

import wsgidav.wsgidav_app
from wsgidav import util
from wsgidav.dav_provider import DAVProvider
from wsgidav.fs_dav_provider import FolderResource, FileResource

from inginious.common.filesystems.local import LocalFSProvider


class WebDavProxy(object):
    """ Redirect webdav requests to the webdav app, and the other requests to the webpy app"""
    def __init__(self, webpy_app, webdav_app):
        self.webpy_app = webpy_app
        self.webdav_app = webdav_app

    def __call__(self, environ, start_response):
        if environ.get("PATH_INFO", "/").startswith("/dav/"):
            return self.webdav_app(environ, start_response)
        else:
            return self.webpy_app(environ, start_response)


class INGIniousDAVDomainController(object):
    """ Authenticates users using the API key and their username """
    def __init__(self, user_manager, course_factory):
        self.course_factory = course_factory
        self.user_manager = user_manager

    def __repr__(self):
        return self.__class__.__name__

    def getDomainRealm(self, inputURL, environ):
        """Resolve a relative url to the  appropriate realm name."""
        # we don't get the realm here, its already been resolved in
        # request_resolver
        if inputURL.startswith("/"):
            inputURL = inputURL[1:]
        parts = inputURL.split("/")
        return parts[0]

    def requireAuthentication(self, realmname, environ):
        """Return True if this realm requires authentication or False if it is
        available for general access."""
        return True

    def isRealmUser(self, realmname, username, environ):
        """Returns True if this username is valid for the realm, False otherwise."""
        try:
            course = self.course_factory.get_course(realmname)
            ok = self.user_manager.has_admin_rights_on_course(course, username=username)
            return ok
        except:
            return False

    def getRealmUserPassword(self, realmname, username, environ):
        """Return the password for the given username for the realm.

        Used for digest authentication.
        """
        return self.user_manager.get_user_api_key(username, create=True)

    def authDomainUser(self, realmname, username, password, environ):
        """Returns True if this username/password pair is valid for the realm,
        False otherwise. Used for basic authentication."""
        try:
            apikey = self.user_manager.get_user_api_key(username, create=None)
            return apikey is not None and password == apikey
        except:
            return False


class INGIniousFilesystemProvider(DAVProvider):
    """ A DAVProvider adapted to the structure of INGInious """
    def __init__(self, course_factory, task_factory):
        super(INGIniousFilesystemProvider, self).__init__()

        self.course_factory = course_factory
        self.task_factory = task_factory
        self.readonly = False

    def _locToFilePath(self, path):
        path_parts = path.strip("/").split("/")

        if len(path_parts) < 1:
            raise RuntimeError("Security exception: tried to access root")

        course_id = path_parts[0]
        try:
            course = self.course_factory.get_course(course_id)
        except:
            raise RuntimeError("Unknown course {}".format(course_id))

        path_to_course_fs = course.get_fs()
        if not isinstance(path_to_course_fs, LocalFSProvider):
            raise RuntimeError("WebDav access is only supported if INGInious is using a local filesystem to access tasks")
        path_to_course = os.path.abspath(path_to_course_fs.prefix)

        file_path = os.path.abspath(os.path.join(path_to_course, *path_parts[1:]))
        if not file_path.startswith(path_to_course):
            raise RuntimeError("Security exception: tried to access file outside course root: {}".format(file_path))

        # Convert to unicode
        file_path = util.toUnicode(file_path)
        return file_path

    def isReadOnly(self):
        return False

    def getResourceInst(self, path, environ):
        """Return info dictionary for path.

        See DAVProvider.getResourceInst()
        """
        self._count_getResourceInst += 1
        fp = self._locToFilePath(path)
        if not os.path.exists(fp):
            return None

        if os.path.isdir(fp):
            return FolderResource(path, environ, fp)
        return FileResource(path, environ, fp)


def init_webdav(user_manager, course_factory, task_factory):
    """ Init the webdav app """

    rp = INGIniousFilesystemProvider(course_factory, task_factory)
    provider_mapping = {}
    provider_mapping["/dav/"] = rp

    config = dict(wsgidav.wsgidav_app.DEFAULT_CONFIG)
    config["provider_mapping"] = provider_mapping
    config["domaincontroller"] = INGIniousDAVDomainController(user_manager, course_factory)
    config["verbose"] = 0

    app = wsgidav.wsgidav_app.WsgiDAVApp(config)

    return app