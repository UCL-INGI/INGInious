# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
from pymongo import MongoClient

from wsgidav import util, wsgidav_app
from wsgidav.dav_provider import DAVProvider
from wsgidav.fs_dav_provider import FolderResource, FileResource

from inginious.common.course_factory import create_factories
from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.user_manager import UserManager
from inginious.frontend.session_mongodb import MongoStore
from inginious.frontend.courses import WebAppCourse
from inginious.frontend.tasks import WebAppTask


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

    def _locToFilePath(self, path, environ=None):
        path_parts = path.strip("/").split("/")

        if len(path_parts) < 1:
            raise RuntimeError("Security exception: tried to access root")

        course_id = path_parts[0]
        try:
            course = self.course_factory.get_course(course_id)
        except:
            raise RuntimeError("Unknown course {}".format(course_id))

        path_to_course_fs = course.get_fs()
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


def get_app(config):
    """ Init the webdav app """
    mongo_client = MongoClient(host=config.get('mongo_opt', {}).get('host', 'localhost'))
    database = mongo_client[config.get('mongo_opt', {}).get('database', 'INGInious')]

    # Create the FS provider
    if "tasks_directory" not in config:
        raise RuntimeError("WebDav access is only supported if INGInious is using a local filesystem to access tasks")

    fs_provider = LocalFSProvider(config["tasks_directory"])
    course_factory, task_factory = create_factories(fs_provider, {}, None, WebAppCourse, WebAppTask)
    user_manager = UserManager(MongoStore(database, 'sessions'), database, config.get('superadmins', []))

    config = dict(wsgidav_app.DEFAULT_CONFIG)
    config["provider_mapping"] = {"/": INGIniousFilesystemProvider(course_factory, task_factory)}
    config["domaincontroller"] = INGIniousDAVDomainController(user_manager, course_factory)
    config["verbose"] = 0

    app = wsgidav_app.WsgiDAVApp(config)

    return app