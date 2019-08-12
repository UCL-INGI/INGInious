# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import sys
from pymongo import MongoClient

from wsgidav import util, wsgidav_app
from wsgidav.dav_error import DAVError, HTTP_NOT_FOUND
from wsgidav.dc.base_dc import BaseDomainController
from wsgidav.dav_provider import DAVProvider
from wsgidav.fs_dav_provider import FolderResource, FileResource

from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.user_manager import UserManager
from inginious.frontend.session_mongodb import MongoStore
from inginious.frontend.courses import WebAppCourse


def get_dc(database, user_manager, filesystem):

    class INGIniousDAVDomainController(BaseDomainController):
        """ Authenticates users using the API key and their username """
        def __init__(self, wsgidav_app, config):
            super(INGIniousDAVDomainController, self).__init__(wsgidav_app, config)

        def __repr__(self):
            return self.__class__.__name__

        def get_domain_realm(self, pathinfo, environ):
            """Resolve a relative url to the  appropriate realm name."""
            # we don't get the realm here, its already been resolved in
            # request_resolver
            if pathinfo.startswith("/"):
                pathinfo = pathinfo[1:]
            parts = pathinfo.split("/")
            return parts[0]

        def require_authentication(self, realm, environ):
            """Return True if this realm requires authentication or False if it is
            available for general access."""
            return True

        def supports_http_digest_auth(self):
            # We don't have access to a plaintext password (or stored hash)
            return False

        def basic_auth_user(self, realmname, username, password, environ):
            """Returns True if this username/password pair is valid for the realm,
            False otherwise. Used for basic authentication."""
            course = database.courses.find_one({"_id": realmname})
            if not course:
                raise DAVError(HTTP_NOT_FOUND, "Could not find '{}'".format(realmname))
            course = WebAppCourse(course["_id"], course, filesystem, None)
            if not user_manager.has_admin_rights_on_course(course, username=username):
                return False
            apikey = user_manager.get_user_api_key(username, create=None)
            return apikey is not None and password == apikey

        def digest_auth_user(self, realm, user_name, environ):
            return False

    return INGIniousDAVDomainController


class INGIniousFilesystemProvider(DAVProvider):
    """ A DAVProvider adapted to the structure of INGInious """
    def __init__(self, database, filesystem):
        super(INGIniousFilesystemProvider, self).__init__()
        self.database = database
        self.filesystem = filesystem
        self.readonly = False

    def _get_course_id(self, path):
        path_parts = self._get_path_parts(path)
        return path_parts[0]

    def _get_inner_path(self, path):
        """ Get the path to the file (as a list of string) beyond the course main folder """
        path_parts = self._get_path_parts(path)
        return path_parts[1:]

    def _get_path_parts(self, path):
        path_parts = path.strip("/").split("/")

        if len(path_parts) < 1:
            raise RuntimeError("Security exception: tried to access root")

        return path_parts

    def _locToFilePath(self, path, environ=None):
        course_id = self._get_course_id(path)
        try:
            course = self.database.courses.find_one({"_id": course_id})
            course = WebAppCourse(course["_id"], course, self.filesystem, None)
        except:
            raise RuntimeError("Unknown course {}".format(course_id))

        path_to_course_fs = course.get_fs()
        path_to_course = os.path.abspath(path_to_course_fs.prefix)

        file_path = os.path.abspath(os.path.join(path_to_course, *self._get_inner_path(path)))
        if not file_path.startswith(path_to_course):
            raise RuntimeError("Security exception: tried to access file outside course root: {}".format(file_path))

        # Convert to unicode
        file_path = util.to_unicode_safe(file_path)
        return file_path

    def is_readonly(self):
        return False

    def get_resource_inst(self, path, environ):
        """Return info dictionary for path.

        See DAVProvider.getResourceInst()
        """
        self._count_get_resource_inst += 1
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
    user_manager = UserManager(MongoStore(database, 'sessions'), database, config.get('superadmins', []))

    config = dict(wsgidav_app.DEFAULT_CONFIG)
    config["provider_mapping"] = {"/": INGIniousFilesystemProvider(database, fs_provider)}
    config["http_authenticator"]["domain_controller"] = get_dc(database, user_manager, fs_provider)
    config["http_authenticator"]["accept_basic"] = True
    config["http_authenticator"]["accept_digest"] = False
    config["http_authenticator"]["default_to_digest"] = False

    app = wsgidav_app.WsgiDAVApp(config)

    return app