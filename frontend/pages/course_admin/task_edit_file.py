# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Allow to create/edit/delete/move/download files associated to tasks """
import mimetypes
import os.path
import tarfile
import tempfile

import web

from common.base import INGIniousConfiguration, id_checker
from common.task_file_managers.manage import get_available_task_file_managers
from frontend.pages.course_admin.utils import get_course_and_check_rights


class CourseTaskFiles(object):

    """ Edit a task """

    def GET(self, courseid, taskid):
        """ Edit a task """
        if not id_checker(taskid):
            raise Exception("Invalid task id")

        get_course_and_check_rights(courseid)

        request = web.input()
        if request.get("action") == "download" and request.get('path') is not None:
            return self.action_download(courseid, taskid, request.get('path'))

    def action_download(self, courseid, taskid, path):
        """ Download a file or a directory """
        task_dir_path = os.path.join(INGIniousConfiguration["tasks_directory"], courseid, taskid)
        # verify that the dir exists
        if not os.path.exists(task_dir_path):
            raise web.notfound()
        wanted_path = os.path.normpath(os.path.join(task_dir_path, path))
        rel_wanted_path = os.path.relpath(wanted_path, task_dir_path)  # normalized
        # verify that the path we want exists and is withing the directory we want
        if not os.path.exists(wanted_path) or os.path.islink(wanted_path) or rel_wanted_path.startswith('..'):
            raise web.notfound()
        # do not allow touching the task.* file
        if os.path.splitext(rel_wanted_path)[0] == "task" and os.path.splitext(rel_wanted_path)[1][1:] in get_available_task_file_managers().keys():
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
                    tar.addfile(info, fileobj=open(os.path.join(root, fname), 'r'))
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
            return open(wanted_path, 'r')
