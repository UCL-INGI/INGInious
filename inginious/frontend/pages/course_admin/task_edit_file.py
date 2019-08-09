# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Allow to create/edit/delete/move/download files associated to tasks """
import json
import os.path

import web

from inginious.common.base import id_checker
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.courses import WebAppCourse

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
        course = self.database.courses.find_one({"_id": courseid})
        course = WebAppCourse(course["_id"], course, self.filesystem, self.plugin_manager)
        return self.template_helper.get_renderer(False).course_admin.edit_tabs.files(
            course, taskid, self.get_task_filelist(self.filesystem, courseid, taskid), error)

    @classmethod
    def get_task_filelist(cls, filesystem, courseid, taskid):
        """ Returns a flattened version of all the files inside the task directory, excluding the files task.* and hidden files.
            It returns a list of tuples, of the type (Integer Level, Boolean IsDirectory, String Name, String CompleteName)
        """
        course_fs = filesystem.from_subfolder(courseid)
        task_fs = course_fs.from_subfolder(taskid)
        if not task_fs.exists():
            return []

        tmp_out = {}
        entries = task_fs.list(True, True, True)
        for entry in entries:
            data = entry.split("/")
            is_directory = False
            if data[-1] == "":
                is_directory = True
                data = data[0:len(data)-1]
            cur_pos = 0
            tree_pos = tmp_out
            while cur_pos != len(data):
                if data[cur_pos] not in tree_pos:
                    tree_pos[data[cur_pos]] = {} if is_directory or cur_pos != len(data) - 1 else None
                tree_pos = tree_pos[data[cur_pos]]
                cur_pos += 1

        def recur_print(current, level, current_name):
            iteritems = sorted(current.items())
            # First, the files
            recur_print.flattened += [(level, False, f, current_name+"/"+f) for f, t in iteritems if t is None]
            # Then, the dirs
            for name, sub in iteritems:
                if sub is not None:
                    recur_print.flattened.append((level, True, name, current_name+"/"+name+"/"))
                    recur_print(sub, level + 1, current_name + "/" + name)
        recur_print.flattened = []
        recur_print(tmp_out, 0, '')
        return recur_print.flattened

    def verify_path(self, courseid, taskid, path, new_path=False):
        """ Return the real wanted path (relative to the INGInious root) or None if the path is not valid/allowed """
        course_fs = self.filesystem.from_subfolder(courseid)
        task_fs = course_fs.from_subfolder(taskid)
        # verify that the dir exists
        if not task_fs.exists():
            return None

        # all path given to this part of the application must start with a "/", let's remove it
        if not path.startswith("/"):
            return None
        path = path[1:len(path)]

        if ".." in path:
            return None

        if task_fs.exists(path) == new_path:
            return None

        # do not allow hidden dir/files
        if path != ".":
            for i in path.split(os.path.sep):
                if i.startswith("."):
                    return None
        return path

    def action_edit(self, courseid, taskid, path):
        """ Edit a file """
        wanted_path = self.verify_path(courseid, taskid, path)
        if wanted_path is None:
            return "Internal error"
        try:
            course_fs = self.filesystem.from_subfolder(courseid)
            task_fs = course_fs.from_subfolder(taskid)
            content = task_fs.get(wanted_path).decode("utf-8")
            return json.dumps({"content": content})
        except:
            return json.dumps({"error": "not-readable"})

    def action_edit_save(self, courseid, taskid, path, content):
        """ Save an edited file """
        wanted_path = self.verify_path(courseid, taskid, path)
        if wanted_path is None:
            return json.dumps({"error": True})
        try:
            course_fs = self.filesystem.from_subfolder(courseid)
            task_fs = course_fs.from_subfolder(taskid)
            task_fs.put(wanted_path, content.encode("utf-8"))
            return json.dumps({"ok": True})
        except:
            return json.dumps({"error": True})

    def action_upload(self, courseid, taskid, path, fileobj):
        """ Upload a file """
        # the path is given by the user. Let's normalize it
        path = path.strip()
        if not path.startswith("/"):
            path = "/" + path
        wanted_path = self.verify_path(courseid, taskid, path, True)
        if wanted_path is None:
            return self.show_tab_file(courseid, taskid, _("Invalid new path"))

        course_fs = self.filesystem.from_subfolder(courseid)
        task_fs = course_fs.from_subfolder(taskid)
        try:
            task_fs.put(wanted_path, fileobj.file.read())
        except:
            return self.show_tab_file(courseid, taskid, _("An error occurred while writing the file"))
        return self.show_tab_file(courseid, taskid)

    def action_create(self, courseid, taskid, path):
        """ Delete a file or a directory """
        # the path is given by the user. Let's normalize it
        path = path.strip()
        if not path.startswith("/"):
            path = "/" + path

        want_directory = path.endswith("/")

        wanted_path = self.verify_path(courseid, taskid, path, True)
        if wanted_path is None:
            return self.show_tab_file(courseid, taskid, _("Invalid new path"))

        course_fs = self.filesystem.from_subfolder(courseid)
        task_fs = course_fs.from_subfolder(taskid)
        if want_directory:
            task_fs.from_subfolder(wanted_path).ensure_exists()
        else:
            task_fs.put(wanted_path, b"")
        return self.show_tab_file(courseid, taskid)

    def action_rename(self, courseid, taskid, path, new_path):
        """ Delete a file or a directory """
        # normalize
        path = path.strip()
        new_path = new_path.strip()
        if not path.startswith("/"):
            path = "/" + path
        if not new_path.startswith("/"):
            new_path = "/" + new_path

        old_path = self.verify_path(courseid, taskid, path)
        if old_path is None:
            return self.show_tab_file(courseid, taskid, _("Internal error"))

        wanted_path = self.verify_path(courseid, taskid, new_path, True)
        if wanted_path is None:
            return self.show_tab_file(courseid, taskid, _("Invalid new path"))

        try:
            course_fs = self.filesystem.from_subfolder(courseid)
            task_fs = course_fs.from_subfolder(taskid)
            task_fs.move(old_path, wanted_path)
            return self.show_tab_file(courseid, taskid)
        except:
            return self.show_tab_file(courseid, taskid, _("An error occurred while moving the files"))

    def action_delete(self, courseid, taskid, path):
        """ Delete a file or a directory """
        # normalize
        path = path.strip()
        if not path.startswith("/"):
            path = "/" + path

        wanted_path = self.verify_path(courseid, taskid, path)
        if wanted_path is None:
            return self.show_tab_file(courseid, taskid, _("Internal error"))

        # special case: cannot delete current directory of the task
        if "/" == wanted_path:
            return self.show_tab_file(courseid, taskid, _("Internal error"))

        try:
            course_fs = self.filesystem.from_subfolder(courseid)
            task_fs = course_fs.from_subfolder(taskid)
            task_fs.delete(wanted_path)
            return self.show_tab_file(courseid, taskid)
        except:
            return self.show_tab_file(courseid, taskid, _("An error occurred while deleting the files"))

    def action_download(self, courseid, taskid, path):
        """ Download a file or a directory """

        wanted_path = self.verify_path(courseid, taskid, path)
        if wanted_path is None:
            raise web.notfound()

        course_fs = self.filesystem.from_subfolder(courseid)
        task_fs = course_fs.from_subfolder(taskid)
        (method, mimetype_or_none, file_or_url) = task_fs.distribute(wanted_path)

        if method == "local":
            web.header('Content-Type', mimetype_or_none)
            return file_or_url
        elif method == "url":
            raise web.redirect(file_or_url)
        else:
            raise web.notfound()


class CourseTaskFileUpload(CourseTaskFiles):

    def POST_AUTH(self, courseid, taskid):
        if not id_checker(taskid):
            raise Exception("Invalid task id")

        self.get_course_and_check_rights(courseid, allow_all_staff=False)

        request = web.input(file={})
        if request.get('file') is not None:
            file = request.get('file')
            name = request.get('name')
            filename = "/"+name
            wanted_path = self.verify_path(courseid, taskid, filename, True)
            self.action_upload(courseid, taskid, wanted_path, file)
            return json.dumps("success")