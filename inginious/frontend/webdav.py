# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import sys
from pymongo import MongoClient
import logging

from wsgidav import util, wsgidav_app, compat
from wsgidav.dav_error import DAVError, HTTP_NOT_FOUND, HTTP_FORBIDDEN
from wsgidav.dc.base_dc import BaseDomainController
from wsgidav.dav_provider import DAVProvider
from wsgidav.fs_dav_provider import FolderResource, FileResource, DAVNonCollection

from inginious.common import custom_yaml
from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.user_manager import UserManager
from inginious.frontend.session_mongodb import MongoStore
from inginious.frontend.courses import WebAppCourse


class FakeIO(object):
    """ Fake fd-like object """
    def __init__(self):
        self._content = None

    def write(self, content):
        self._content = content

    def close(self):
        pass

    def getvalue(self):
        return self._content


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
            course = database.courses.find_one({"_id": realm})
            if not course:
                return False
            return True

        def supports_http_digest_auth(self):
            # We have access to a plaintext password (or stored hash)
            return True

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
            """Computes digest hash A1 part."""
            password = user_manager.get_user_api_key(user_name, create=True)
            return self._compute_http_digest_a1(realm, user_name, password)

    return INGIniousDAVDomainController


class INGIniousTaskFile(DAVNonCollection):
    """ Protects the course description file. """
    def __init__(self, path, environ, database, course_id, task_id):
        super(INGIniousTaskFile, self).__init__(path, environ)
        self._database = database
        self._course_id = course_id
        self._task_id = task_id
        self._content = FakeIO()

    def support_recursive_delete(self):
        return False

    def get_content_length(self):
        return len(self.get_content().read())

    def get_content_type(self):
        return "text/yaml"

    def get_content(self):
        task_desc = self._database.tasks.find_one({"courseid": self._course_id, "taskid": self._task_id})
        if task_desc:
            del task_desc["courseid"]
            del task_desc["taskid"]
            del task_desc["_id"]
            logger = logging.getLogger("inginious.webdav")
            logger.info("Exporting task {}/{}".format(self._course_id, self._task_id))
            return compat.BytesIO(custom_yaml.dump(task_desc).encode("utf-8"))
        return compat.BytesIO(b"")

    def delete(self):
        """ It is forbidden to delete a course description file"""
        self._database.tasks.delete_one({"courseid": self._course_id, "taskid": self._task_id})
        self.remove_all_properties(True)
        self.remove_all_locks(True)

    def copy_move_single(self, dest_path, is_move):
        """ It is forbidden to delete a course description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def move_recursive(self, dest_path):
        """ It is forbidden to delete a course description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def begin_write(self, content_type=None):
        return self._content

    def end_write(self, with_errors):
        """ Update the course.yaml if possible. Verifies the content first, and make backups beforehand. """
        logger = logging.getLogger("inginious.webdav")
        logger.info("Importing task {}/{}".format(self._course_id, self._task_id))
        task_desc = custom_yaml.load(self._content.getvalue())
        task_desc["courseid"] = self._course_id
        task_desc["taskid"] = self._task_id
        if self._database.tasks.find_one({"courseid": self._course_id, "taskid": self._task_id}):
            self._database.tasks.replace_one({"courseid": self._course_id, "taskid": self._task_id}, task_desc)
        else:
            self._database.tasks.insert(task_desc)


class INGIniousTaskFolder(FolderResource):
    def __init__(self, path, environ, file_path, database, course_id, task_id):
        super(INGIniousTaskFolder, self).__init__(path, environ, file_path)
        self._database = database
        self._course_id = course_id
        self._task_id = task_id

    def get_member_names(self):
        names = super(INGIniousTaskFolder, self).get_member_names()
        task_desc = self._database.tasks.find_one({"courseid": self._course_id, "taskid": self._task_id})
        if task_desc:
            return names + ["task.yaml"]
        else:
            return names

    def get_member(self, name):
        if name == "task.yaml":
            fp = os.path.join(self._file_path, compat.to_unicode(name))
            path = util.join_uri(self.path, name)
            return INGIniousTaskFile(path, self.environ, self._database, self._course_id, self._task_id)
        else:
            return super(INGIniousTaskFolder, self).get_member(name)

    def create_empty_resource(self, name):
        if name == "task.yaml":
            fp = os.path.join(self._file_path, compat.to_unicode(name))
            path = util.join_uri(self.path, name)
            return INGIniousTaskFile(path, self.environ, self._database, self._course_id, self._task_id)
        else:
            return super(INGIniousTaskFolder, self).create_empty_resource(name)


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

    def _loc_to_file_path(self, path, environ=None):
        course_id = self._get_course_id(path)
        try:
            course = self.database.courses.find_one({"_id": course_id})
            course = WebAppCourse(course["_id"], course, self.filesystem, None)
        except:
            raise DAVError(HTTP_NOT_FOUND, "Unknown course {}".format(course_id))

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
        fp = self._loc_to_file_path(path)
        inner_path = self._get_inner_path(path)

        if len(inner_path) == 2 and inner_path[1] == "task.yaml":
            task_desc = self.database.tasks.find_one({"courseid": self._get_course_id(path), "taskid": inner_path[0]})
            if task_desc:
                return INGIniousTaskFile(path, environ, self.database, self._get_course_id(path), inner_path[0])
            else:
                return None

        if not os.path.exists(fp):
            return None

        if os.path.isdir(fp):
            if len(inner_path) == 1:
                return INGIniousTaskFolder(path, environ, fp, self.database, self._get_course_id(path), inner_path[0])
            else:
                return FolderResource(path, environ, fp)

        # course.yaml needs a special protection
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
    config["verbose"] = 0

    app = wsgidav_app.WsgiDAVApp(config)
    util.init_logging(config)

    return app