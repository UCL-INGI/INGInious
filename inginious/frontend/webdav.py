# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
from pymongo import MongoClient

from wsgidav import util, wsgidav_app
from wsgidav.dav_error import DAVError, HTTP_NOT_FOUND, HTTP_FORBIDDEN
from wsgidav.dc.base_dc import BaseDomainController
from wsgidav.dav_provider import DAVProvider
from wsgidav.fs_dav_provider import FolderResource, FileResource

from inginious.frontend.taskset_factory import create_factories
from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.user_manager import UserManager

def get_dc(taskset_factory, user_manager, filesystem):

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
            # We have access to a plaintext password (or stored hash)
            return True

        def is_user_realm_admin(self, realm, user_name):
            try:
                taskset = taskset_factory.get_taskset(realm)
            except Exception as ex:
                return True  # Not a taskset: static file,...

            return user_name in taskset.get_admins() or user_manager.user_is_superadmin(user_name)

        def basic_auth_user(self, realm, user_name, password, environ):
            if not self.is_user_realm_admin(realm, user_name):
                return False
            apikey = user_manager.get_user_api_key(user_name, create=True)
            return apikey is not None and password == apikey

        def digest_auth_user(self, realm, user_name, environ):
            """Computes digest hash A1 part."""
            if not self.is_user_realm_admin(realm, user_name):
                return False
            password = user_manager.get_user_api_key(user_name, create=True) or ''
            return self._compute_http_digest_a1(realm, user_name, password)

    return INGIniousDAVDomainController

class INGIniousDAVCourseFile(FileResource):
    """ Protects the taskset description file. """
    def __init__(self, path, environ, filePath, taskset_factory, taskset_id):
        super(INGIniousDAVCourseFile, self).__init__(path, environ, filePath)
        self._taskset_factory = taskset_factory
        self._taskset_id = taskset_id

    def delete(self):
        """ It is forbidden to delete a taskset description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def copy_move_single(self, dest_path, is_move):
        """ It is forbidden to delete a taskset description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def move_recursive(self, dest_path):
        """ It is forbidden to delete a taskset description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def begin_write(self, content_type=None):
        """Open content as a stream for writing. Do not put the content into taskset.yaml directly."""

        # In order to avoid to temporarily lose the content of the file, we write somewhere else.
        # endWrite will be in charge of putting the content in the correct file, after verifying its content.
        return open(self._file_path + ".webdav_tmp", "wb", 8192)

    def end_write(self, with_errors):
        """ Update the taskset.yaml if possible. Verifies the content first, and make backups beforehand. """

        if with_errors:
            # something happened while uploading, let's remove the tmp file
            os.remove(self._file_path + ".webdav_tmp")
        else:
            # get the original content of the file
            with open(self._file_path, "rb") as orig_file:
                orig_content = orig_file.read()
            # get the new content that just has been uploaded
            with open(self._file_path + ".webdav_tmp", "rb") as new_file:
                new_content = new_file.read()
            os.remove(self._file_path + ".webdav_tmp") #the file is not needed anymore

            # backup the original content. In case inginious-webdav crashes while updating the file.
            with open(self._file_path + ".webdav_backup", "wb", 8192) as backup_file:
                backup_file.write(orig_content)

            # Put the new content in the file, temporarily
            with open(self._file_path, "wb", 8192) as orig_file:
                orig_file.write(new_content)

            # Now we check if we can still load the taskset...
            try:
                self._taskset_factory.get_taskset(self._taskset_id)
                # Everything ok, let's leave things as-is
            except:
                # We can't load the new file, rollback!
                with open(self._file_path, "wb", 8192) as orig_file:
                    orig_file.write(orig_content)

            # Remove the unneeded backup
            os.remove(self._file_path + ".webdav_backup")


class INGIniousFilesystemProvider(DAVProvider):
    """ A DAVProvider adapted to the structure of INGInious """
    def __init__(self, taskset_factory, task_factory):
        super(INGIniousFilesystemProvider, self).__init__()

        self.taskset_factory = taskset_factory
        self.task_factory = task_factory
        self.readonly = False

    def _get_taskset_id(self, path):
        path_parts = self._get_path_parts(path)
        return path_parts[0]

    def _get_inner_path(self, path):
        """ Get the path to the file (as a list of string) beyond the taskset main folder """
        path_parts = self._get_path_parts(path)
        return path_parts[1:]

    def _get_path_parts(self, path):
        path_parts = path.strip("/").split("/")

        if len(path_parts) < 1:
            raise RuntimeError("Security exception: tried to access root")

        return path_parts

    def _loc_to_file_path(self, path, environ=None):
        taskset_id = self._get_taskset_id(path)
        try:
            taskset = self.taskset_factory.get_taskset(taskset_id)
        except:
            raise DAVError(HTTP_NOT_FOUND, "Unknown taskset {}".format(taskset_id))

        path_to_taskset_fs = taskset.get_fs()
        path_to_taskset = os.path.abspath(path_to_taskset_fs.prefix)

        file_path = os.path.abspath(os.path.join(path_to_taskset, *self._get_inner_path(path)))
        if not file_path.startswith(path_to_taskset):
            raise RuntimeError("Security exception: tried to access file outside taskset root: {}".format(file_path))

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
        if not os.path.exists(fp):
            return None

        if os.path.isdir(fp):
            return FolderResource(path, environ, fp)

        # taskset.yaml needs a special protection
        inner_path = self._get_inner_path(path)
        if len(inner_path) == 1 and inner_path[0] in ["taskset.yaml", "course.yaml", "course.json"]:
            return INGIniousDAVCourseFile(path, environ, fp, self.taskset_factory, self._get_taskset_id(path))

        return FileResource(path, environ, fp)


def get_app(config):
    """ Init the webdav app """
    mongo_client = MongoClient(host=config.get('mongo_opt', {}).get('host', 'localhost'))
    database = mongo_client[config.get('mongo_opt', {}).get('database', 'INGInious')]

    # Create the FS provider
    if "tasks_directory" not in config:
        raise RuntimeError("WebDav access is only supported if INGInious is using a local filesystem to access tasks")

    fs_provider = LocalFSProvider(config["tasks_directory"])
    taskset_factory, _, task_factory = create_factories(fs_provider, {}, {}, None)
    user_manager = UserManager(database, config.get('superadmins', []))

    config = dict(wsgidav_app.DEFAULT_CONFIG)
    config["provider_mapping"] = {"/": INGIniousFilesystemProvider(taskset_factory, task_factory)}
    config["http_authenticator"]["domain_controller"] = get_dc(taskset_factory, user_manager, fs_provider)
    config["verbose"] = 0

    app = wsgidav_app.WsgiDAVApp(config)
    util.init_logging(config)

    return app