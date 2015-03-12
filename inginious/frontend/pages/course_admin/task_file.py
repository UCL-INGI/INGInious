# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
""" Send a zip file containing course data """
from StringIO import StringIO
import os.path
import zipfile
import web
from inginious.common.base import INGIniousConfiguration, id_checker
from inginious.common.task_file_managers.tasks_file_manager import TaskFileManager
from inginious.frontend.pages.course_admin.utils import get_course_and_check_rights


def make_zipfile(output_filename, source_dir, exclude):
    """
        Make a new zipfile from a source_dir, excluding files in the "exclude" list.
        Source: http://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory-in-python
    """
    exclude = [os.path.abspath(os.path.join(source_dir, f)) for f in exclude]
    relroot = os.path.abspath(os.path.join(source_dir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zipf.write(root, os.path.relpath(root, relroot))
            for dfile in files:
                if os.path.abspath(os.path.join(root, dfile)) in exclude:
                    continue
                filename = os.path.join(root, dfile)
                if os.path.isfile(filename):  # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), dfile)
                    zipf.write(filename, arcname)


class DownloadTaskFiles(object):

    """ Send a zip file containing course data """

    def GET(self, courseid, taskid):
        """ GET """
        if not id_checker(taskid):
            raise Exception("Invalid task id")
        if not id_checker(courseid):
            raise Exception("Invalid task id")

        # Check rights
        get_course_and_check_rights(courseid)

        exclude = ["task.{}".format(subclass.get_ext()) for subclass in TaskFileManager.__subclasses__()]
        dir_path = os.path.join(INGIniousConfiguration["tasks_directory"], courseid, taskid)

        stringio = StringIO()
        make_zipfile(stringio, dir_path, exclude)
        web.header('Content-Type', 'application/zip')
        web.header('Content-disposition', 'attachment; filename={}-{}.zip'.format(courseid, taskid))
        return stringio.getvalue()
