# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
from pymongo import MongoClient

from wsgidav import util, wsgidav_app
from wsgidav.dav_error import DAVError, HTTP_FORBIDDEN
from wsgidav.dav_provider import DAVProvider
from wsgidav.fs_dav_provider import FolderResource, FileResource

from inginious.common.course_factory import create_factories
from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.user_manager import UserManager
from inginious.frontend.session_mongodb import MongoStore
from inginious.frontend.courses import WebAppCourse
from inginious.frontend.tasks import WebAppTask


class INGIniousDAVCourseFile(FileResource):
    """ Protects the course description file. """
    def __init__(self, path, environ, filePath, course_factory, course_id):
        super(INGIniousDAVCourseFile, self).__init__(path, environ, filePath)
        self._course_factory = course_factory
        self._course_id = course_id

    def delete(self):
        """ It is forbidden to delete a course description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def copyMoveSingle(self, destPath, isMove):
        """ It is forbidden to delete a course description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def moveRecursive(self, destPath):
        """ It is forbidden to delete a course description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def beginWrite(self, contentType=None):
        """Open content as a stream for writing. Do not put the content into course.yaml directly."""

        # In order to avoid to temporarily lose the content of the file, we write somewhere else.
        # endWrite will be in charge of putting the content in the correct file, after verifying its content.
        return open(self._filePath+".webdav_tmp", "wb", 8192)

    def endWrite(self, withErrors):
        """ Update the course.yaml if possible. Verifies the content first, and make backups beforehand. """

        if withErrors:
            # something happened while uploading, let's remove the tmp file
            os.remove(self._filePath+".webdav_tmp")
        else:
            # get the original content of the file
            with open(self._filePath, "rb") as orig_file:
                orig_content = orig_file.read()
            # get the new content that just has been uploaded
            with open(self._filePath+".webdav_tmp", "rb") as new_file:
                new_content = new_file.read()
            os.remove(self._filePath + ".webdav_tmp") #the file is not needed anymore

            # backup the original content. In case inginious-webdav crashes while updating the file.
            with open(self._filePath + ".webdav_backup", "wb", 8192) as backup_file:
                backup_file.write(orig_content)

            # Put the new content in the file, temporarily
            with open(self._filePath, "wb", 8192) as orig_file:
                orig_file.write(new_content)

            # Now we check if we can still load the course...
            try:
                self._course_factory.get_course(self._course_id)
                # Everything ok, let's leave things as-is
            except:
                # We can't load the new file, rollback!
                with open(self._filePath, "wb", 8192) as orig_file:
                    orig_file.write(orig_content)

            # Remove the unneeded backup
            os.remove(self._filePath + ".webdav_backup")


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
            course = self.course_factory.get_course(course_id)
        except:
            raise RuntimeError("Unknown course {}".format(course_id))

        path_to_course_fs = course.get_fs()
        path_to_course = os.path.abspath(path_to_course_fs.prefix)

        file_path = os.path.abspath(os.path.join(path_to_course, *self._get_inner_path(path)))
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

        # course.yaml needs a special protection
        inner_path = self._get_inner_path(path)
        if len(inner_path) == 1 and inner_path[0] in ["course.yaml", "course.json"]:
            return INGIniousDAVCourseFile(path, environ, fp, self.course_factory, self._get_course_id(path))

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