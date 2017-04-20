# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Allow to create/edit/delete/move/download files associated to tasks """
import codecs
import json
import mimetypes
import os.path
import shutil
import tarfile
import tempfile

import web

from inginious.common.base import id_checker
from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage


class CourseTaskFiles(INGIniousAdminPage):
    """ Edit a task """

    def GET_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ
        """ Edit a task """
        if not id_checker(taskid):
            raise Exception("Invalid task id")

        self.get_course_and_check_rights(courseid, allow_all_staff=False)

        request = web.input()
        if request.get("action") == "download" and request.get('path') is not None:
            return self.action_download(courseid, taskid, request.get('path'))
        elif request.get("action") == "delete" and request.get('path') is not None:
            return self.action_delete(courseid, taskid, request.get('path'))
        elif request.get("action") == "rename" and request.get('path') is not None and request.get('new_path') is not None:
            return self.action_rename(courseid, taskid, request.get('path'), request.get('new_path'))
        elif request.get("action") == "create" and request.get('path') is not None:
            return self.action_create(courseid, taskid, request.get('path'))
        elif request.get("action") == "edit" and request.get('path') is not None:
            return self.action_edit(courseid, taskid, request.get('path'))
        else:
            return self.show_tab_file(courseid, taskid)

    def POST_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ
        """ Upload or modify a file """
        if not id_checker(taskid):
            raise Exception("Invalid task id")

        self.get_course_and_check_rights(courseid, allow_all_staff=False)

        request = web.input(file={})
        if request.get("action") == "upload" and request.get('path') is not None and request.get('file') is not None:
            return self.action_upload(courseid, taskid, request.get('path'), request.get('file'))
        elif request.get("action") == "edit_save" and request.get('path') is not None and request.get('content') is not None:
            return self.action_edit_save(courseid, taskid, request.get('path'), request.get('content'))
        else:
            return self.show_tab_file(courseid, taskid)

    def show_tab_file(self, courseid, taskid, error=None):
        """ Return the file tab """
        return self.template_helper.get_renderer(False).course_admin.edit_tabs.files(
            self.course_factory.get_course(courseid), taskid, self.get_task_filelist(self.task_factory, courseid, taskid), error)

    @classmethod
    def get_task_filelist(cls, task_factory, courseid, taskid):
        """ Returns a flattened version of all the files inside the task directory, excluding the files task.* and hidden files.
            It returns a list of tuples, of the type (Integer Level, Boolean IsDirectory, String Name, String CompleteName)
        """
        path = task_factory.get_directory_path(courseid, taskid)
        if not os.path.exists(path):
            return []
        result_dict = {}
        for root, _, files in os.walk(path):
            rel_root = os.path.normpath(os.path.relpath(root, path))
            insert_dict = result_dict
            if rel_root != ".":
                hidden_dir = False
                for i in rel_root.split(os.path.sep):
                    if i.startswith("."):
                        hidden_dir = True
                        break
                    if i not in insert_dict:
                        insert_dict[i] = {}
                    insert_dict = insert_dict[i]
                if hidden_dir:
                    continue
            for f in files:
                # Do not follow symlinks and do not take into account task describers
                if not os.path.islink(os.path.join(root, f)) and \
                        not (root == path and os.path.splitext(f)[0] == "task"
                             and os.path.splitext(f)[1][1:] in task_factory.get_available_task_file_extensions()) \
                        and not f.startswith("."):
                    insert_dict[f] = None

        def recur_print(current, level, current_name):
            iteritems = sorted(current.items())
            # First, the files
            recur_print.flattened += [(level, False, f, os.path.join(current_name, f)) for f, t in iteritems if t is None]
            # Then, the dirs
            for name, sub in iteritems:
                if sub is not None:
                    recur_print.flattened.append((level, True, name, os.path.join(current_name, name)))
                    recur_print(sub, level + 1, os.path.join(current_name, name))

        recur_print.flattened = []
        recur_print(result_dict, 0, '')
        return recur_print.flattened

    def verify_path(self, courseid, taskid, path, new_path=False):
        """ Return the real wanted path (relative to the INGInious root) or None if the path is not valid/allowed """

        task_dir_path = self.task_factory.get_directory_path(courseid, taskid)
        # verify that the dir exists
        if not os.path.exists(task_dir_path):
            return None
        wanted_path = os.path.normpath(os.path.join(task_dir_path, path))
        rel_wanted_path = os.path.relpath(wanted_path, task_dir_path)  # normalized
        # verify that the path we want exists and is withing the directory we want
        if (new_path == os.path.exists(wanted_path)) or os.path.islink(wanted_path) or rel_wanted_path.startswith('..'):
            return None
        # do not allow touching the task.* file
        if os.path.splitext(rel_wanted_path)[0] == "task" and os.path.splitext(rel_wanted_path)[1][1:] in \
                self.task_factory.get_available_task_file_extensions():
            return None
        # do not allow hidden dir/files
        if rel_wanted_path != ".":
            for i in rel_wanted_path.split(os.path.sep):
                if i.startswith("."):
                    return None
        return wanted_path

    def action_edit(self, courseid, taskid, path):
        """ Edit a file """
        wanted_path = self.verify_path(courseid, taskid, path)
        if wanted_path is None or not os.path.isfile(wanted_path):
            return "Internal error"
        try:
            content = open(wanted_path, 'r').read()
            return json.dumps({"content": content})
        except:
            return json.dumps({"error": "not-readable"})

    def action_edit_save(self, courseid, taskid, path, content):
        """ Save an edited file """
        wanted_path = self.verify_path(courseid, taskid, path)
        if wanted_path is None or not os.path.isfile(wanted_path):
            return json.dumps({"error": True})

        try:
            with codecs.open(wanted_path, "w", "utf-8") as f:
                f.write(content)
            return json.dumps({"ok": True})
        except:
            return json.dumps({"error": True})

    def action_upload(self, courseid, taskid, path, fileobj):
        """ Upload a file """

        wanted_path = self.verify_path(courseid, taskid, path, True)
        if wanted_path is None:
            return self.show_tab_file(courseid, taskid, "Invalid new path")
        curpath = self.task_factory.get_directory_path(courseid, taskid)
        rel_path = os.path.relpath(wanted_path, curpath)

        for i in rel_path.split(os.path.sep)[:-1]:
            curpath = os.path.join(curpath, i)
            if not os.path.exists(curpath):
                os.mkdir(curpath)
            if not os.path.isdir(curpath):
                return self.show_tab_file(courseid, taskid, i + " is not a directory!")

        try:
            open(wanted_path, "wb").write(fileobj.file.read())
            return self.show_tab_file(courseid, taskid)
        except:
            return self.show_tab_file(courseid, taskid, "An error occurred while writing the file")

    def action_create(self, courseid, taskid, path):
        """ Delete a file or a directory """

        want_directory = path.strip().endswith("/")

        wanted_path = self.verify_path(courseid, taskid, path, True)
        if wanted_path is None:
            return self.show_tab_file(courseid, taskid, "Invalid new path")
        curpath = self.task_factory.get_directory_path(courseid, taskid)
        rel_path = os.path.relpath(wanted_path, curpath)

        for i in rel_path.split(os.path.sep)[:-1]:
            curpath = os.path.join(curpath, i)
            if not os.path.exists(curpath):
                os.mkdir(curpath)
            if not os.path.isdir(curpath):
                return self.show_tab_file(courseid, taskid, i + " is not a directory!")
        if rel_path.split(os.path.sep)[-1] != "":
            if want_directory:
                os.mkdir(os.path.join(curpath, rel_path.split(os.path.sep)[-1]))
            else:
                open(os.path.join(curpath, rel_path.split(os.path.sep)[-1]), 'a')
        return self.show_tab_file(courseid, taskid)

    def action_rename(self, courseid, taskid, path, new_path):
        """ Delete a file or a directory """

        old_path = self.verify_path(courseid, taskid, path)
        if old_path is None:
            return self.show_tab_file(courseid, taskid, "Internal error")

        wanted_path = self.verify_path(courseid, taskid, new_path, True)
        if wanted_path is None:
            return self.show_tab_file(courseid, taskid, "Invalid new path")

        try:
            shutil.move(old_path, wanted_path)
            return self.show_tab_file(courseid, taskid)
        except:
            return self.show_tab_file(courseid, taskid, "An error occurred while moving the files")

    def action_delete(self, courseid, taskid, path):
        """ Delete a file or a directory """

        wanted_path = self.verify_path(courseid, taskid, path)
        if wanted_path is None:
            return self.show_tab_file(courseid, taskid, "Internal error")

        # special case: cannot delete current directory of the task
        if "." == os.path.relpath(wanted_path, self.task_factory.get_directory_path(courseid, taskid)):
            return self.show_tab_file(courseid, taskid, "Internal error")

        if os.path.isdir(wanted_path):
            shutil.rmtree(wanted_path)
        else:
            os.unlink(wanted_path)
        return self.show_tab_file(courseid, taskid)

    def action_download(self, courseid, taskid, path):
        """ Download a file or a directory """

        wanted_path = self.verify_path(courseid, taskid, path)
        if wanted_path is None:
            raise web.notfound()

        # if the user want a dir:
        if os.path.isdir(wanted_path):
            tmpfile = tempfile.TemporaryFile()
            tar = tarfile.open(fileobj=tmpfile, mode='w:gz')
            for root, _, files in os.walk(wanted_path):
                for fname in files:
                    info = tarfile.TarInfo(name=os.path.join(os.path.relpath(root, wanted_path), fname))
                    file_stat = os.stat(os.path.join(root, fname))
                    info.size = file_stat.st_size
                    info.mtime = file_stat.st_mtime
                    tar.addfile(info, fileobj=open(os.path.join(root, fname), 'rb'))
            tar.close()
            tmpfile.seek(0)
            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="dir.tgz"', unique=True)
            return tmpfile
        else:
            mimetypes.init()
            mime_type = mimetypes.guess_type(wanted_path)
            web.header('Content-Type', mime_type[0])
            web.header('Content-Disposition', 'attachment; filename="' + os.path.split(wanted_path)[1] + '"', unique=True)
            return open(wanted_path, 'rb')
